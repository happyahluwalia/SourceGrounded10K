from typing import Literal, Optional, Any
from pathlib import Path
import logging
import json

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_ollama import ChatOllama

from app.core.config import settings
from app.tools.filing_qa_tool import answer_filing_question

logger = logging.getLogger(__name__)

class SupervisorAgent:
    """
    The main Supervisor agent that orchestrates all other tools and agents.
    For now, its only tool is the comprehensive FilingQATool.
    
    The agent uses AsyncPostgresSaver for checkpointing, which is initialized
    at the application level and reused across requests for efficiency.
    """
    
    # Class-level checkpointer (singleton pattern)
    _checkpointer: Optional[AsyncPostgresSaver] = None
    _checkpointer_cm: Optional[Any] = None  # Context manager for cleanup
    _checkpointer_initialized: bool = False
    
    def __init__(self):
        """
        Initializes the SupervisorAgent, building the graph definition.
        The graph is not compiled here to allow for just-in-time compilation with a checkpointer.
        """
        self.model_name = settings.supervisor_model
        self.tools = [answer_filing_question]
        self.tools_by_name = {tool.name: tool for tool in self.tools}

        self.llm = ChatOllama(
            model=self.model_name,
            base_url=settings.ollama_base_url,
            temperature=0.1
        )
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Build the graph definition
        self.graph_builder = self._build_graph_definition()
    
    @classmethod
    async def initialize_checkpointer(cls) -> None:
        """
        Initialize the checkpointer at application startup.
        This method is idempotent - safe to call multiple times.
        
        Must be called before using ainvoke().
        """
        if cls._checkpointer_initialized:
            logger.info("Checkpointer already initialized, skipping")
            return
        
        try:
            logger.info("Initializing AsyncPostgresSaver checkpointer...")
            
            # Create checkpointer connection (keep it open for reuse)
            # We manually enter the async context manager and store it
            cls._checkpointer_cm = AsyncPostgresSaver.from_conn_string(settings.database_url)
            cls._checkpointer = await cls._checkpointer_cm.__aenter__()
            
            # Run setup to create tables (idempotent operation)
            await cls._checkpointer.setup()
            logger.info("✓ Checkpoint tables created/verified")
            
            cls._checkpointer_initialized = True
            logger.info("✓ Checkpointer initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize checkpointer: {e}", exc_info=True)
            # Cleanup if context manager was entered
            if cls._checkpointer_cm:
                try:
                    await cls._checkpointer_cm.__aexit__(None, None, None)
                except Exception as cleanup_error:
                    logger.warning(f"Error during cleanup after failed init: {cleanup_error}")
            cls._checkpointer = None
            cls._checkpointer_cm = None
            cls._checkpointer_initialized = False
            raise RuntimeError(f"Checkpointer initialization failed: {e}")
    
    @classmethod
    async def cleanup_checkpointer(cls) -> None:
        """
        Cleanup checkpointer resources on application shutdown.
        """
        if cls._checkpointer and cls._checkpointer_cm:
            logger.info("Cleaning up checkpointer resources...")
            try:
                # Properly exit the async context manager
                await cls._checkpointer_cm.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error during checkpointer cleanup: {e}")
            finally:
                cls._checkpointer = None
                cls._checkpointer_cm = None
                cls._checkpointer_initialized = False
                logger.info("✓ Checkpointer cleanup complete")
    
    @classmethod
    def get_checkpointer(cls) -> AsyncPostgresSaver:
        """
        Get the initialized checkpointer instance.
        
        Raises:
            RuntimeError: If checkpointer not initialized
        """
        if not cls._checkpointer_initialized or cls._checkpointer is None:
            raise RuntimeError(
                "Checkpointer not initialized. Call initialize_checkpointer() at startup."
            )
        return cls._checkpointer

    def _build_graph_definition(self):
        """Builds the LangGraph state machine definition."""
        graph_builder = StateGraph(MessagesState)
        
        # Define nodes
        graph_builder.add_node("supervisor_llm", self._llm_call)
        graph_builder.add_node("specialist_tool", self._tool_node)
        
        # Define edges
        graph_builder.add_edge(START, "supervisor_llm")
        graph_builder.add_conditional_edges(
            "supervisor_llm",
            self._should_continue,
            {"tool_node": "specialist_tool", END: END}
        )
        graph_builder.add_edge("specialist_tool", END)
        
        return graph_builder

    # Node implementations
    def _llm_call(self, state: MessagesState):
        """The supervisor LLM decides which tool to call."""
        try:
            prompt_path = Path(__file__).parent.parent / "prompts" / "supervisor.txt"
            system_prompt = prompt_path.read_text()
        except FileNotFoundError:
            logger.error("Supervisor prompt file not found.")
            system_prompt = "You are a helpful assistant. Use the tools available to answer the user's question."

        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        response = self.llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def _tool_node(self, state: MessagesState):
        """Executes the tool chosen by the supervisor."""
        result = []
        last_message = state["messages"][-1]
        for tool_call in last_message.tool_calls:
            tool = self.tools_by_name[tool_call["name"]]
            observation = tool.invoke(tool_call["args"])
            result.append(ToolMessage(content=str(observation), tool_call_id=tool_call["id"]))
        return {"messages": result}

    def _should_continue(self, state: MessagesState) -> Literal["tool_node", END]:
        """Routes to tool execution or ends the process."""
        return "tool_node" if state["messages"][-1].tool_calls else END


    async def ainvoke(
        self, 
        query: str, 
        user_id: Optional[str] = None, 
        session_id: Optional[str] = None
    ) -> dict:
        """
        Processes a query asynchronously with checkpointing.
        
        Args:
            query: The user's question
            user_id: Optional user identifier (defaults to 'anonymous')
            session_id: Session ID for conversation continuity (required for checkpointing)
        
        Returns:
            dict with 'query', 'answer', 'messages', and 'session_id'
        
        Raises:
            RuntimeError: If checkpointer not initialized
            Exception: For other processing errors
        """
        try:
            # Validate session_id for checkpointing
            if not session_id:
                logger.warning("No session_id provided, generating new one")
                import uuid
                session_id = str(uuid.uuid4())
            
            messages = [HumanMessage(content=query)]
            thread_id = f"{user_id or 'anonymous'}_{session_id}"
            config = {"configurable": {"thread_id": thread_id}}
            
            logger.info(f"Processing query for thread_id: {thread_id}")
            
            # Get the shared checkpointer instance
            checkpointer = self.get_checkpointer()
            
            # Compile graph with checkpointer and execute
            graph = self.graph_builder.compile(checkpointer=checkpointer)
            result = await graph.ainvoke({"messages": messages}, config=config)
            
            # Extract final answer from tool messages
            final_answer = "Could not process the request."
            for msg in reversed(result['messages']):
                if isinstance(msg, ToolMessage):
                    tool_response = msg.content
                    # Try to parse JSON response from tools (especially filing_qa_tool)
                    try:
                        parsed_response = json.loads(tool_response)
                        final_answer = parsed_response  # Return structured object
                        logger.info("✓ Parsed structured response from tool")
                    except (json.JSONDecodeError, TypeError):
                        # If not JSON, use as plain text (backward compatibility)
                        final_answer = tool_response
                        logger.info("Using tool response as plain text")
                    break
            
            logger.info(f"✓ Query processed successfully for thread_id: {thread_id}")
            
            return {
                "query": query,
                "answer": final_answer,
                "messages": result['messages'],
                "session_id": session_id  # Return session_id for frontend to store
            }
            
        except RuntimeError as e:
            logger.error(f"Checkpointer error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            raise Exception(f"Failed to process query: {str(e)}")
    
    async def astream_response(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """
        Stream events from graph execution for real-time UI updates.
        
        Yields different event types:
        - {"type": "token", "content": "word", "session_id": "..."}
        - {"type": "tool_start", "tool": "answer_filing_question", "session_id": "..."}
        - {"type": "tool_end", "tool": "answer_filing_question", "session_id": "..."}
        - {"type": "complete", "answer": "full answer", "session_id": "..."}
        - {"type": "error", "message": "error details", "session_id": "..."}
        
        Args:
            query: The user's question
            user_id: Optional user identifier
            session_id: Session ID for conversation continuity
            
        Yields:
            dict: Event objects with type and relevant data
        """
        try:
            # Validate session_id
            if not session_id:
                import uuid
                session_id = str(uuid.uuid4())
            
            messages = [HumanMessage(content=query)]
            thread_id = f"{user_id or 'anonymous'}_{session_id}"
            config = {"configurable": {"thread_id": thread_id}}
            
            logger.info(f"Streaming query for thread_id: {thread_id}")
            
            # Get checkpointer and compile graph
            checkpointer = self.get_checkpointer()
            graph = self.graph_builder.compile(checkpointer=checkpointer)
            
            accumulated_answer = ""
            current_step = None
            step_start_time = None
            sources = []  # Store sources from tool output
            
            # Stream events from graph execution
            async for event in graph.astream_events(
                {"messages": messages},
                config=config,
                version="v2"
            ):
                event_type = event.get("event")
                event_name = event.get("name", "")
                
                # Detect planning step (first LLM call is supervisor deciding which tool to use)
                if event_type == "on_chat_model_start":
                    import time
                    if current_step is None:
                        current_step = "planning"
                        step_start_time = time.time()
                        yield {
                            "type": "step_start",
                            "step": "planning",
                            "session_id": session_id
                        }
                
                # Don't stream LLM tokens - the tool returns complete answer
                # Streaming individual tokens would require refactoring the tool
                
                # Tool execution started
                elif event_type == "on_tool_start":
                    tool_name = event.get("name", "unknown")
                    logger.info(f"🔧 Tool started: {tool_name}")
                    
                    # Emit fetching step when tool starts
                    if current_step != "fetching":
                        import time
                        current_step = "fetching"
                        step_start_time = time.time()
                        yield {
                            "type": "step_start",
                            "step": "fetching",
                            "session_id": session_id
                        }
                    
                    yield {
                        "type": "tool_start",
                        "tool": tool_name,
                        "session_id": session_id
                    }
                
                # Tool execution completed
                elif event_type == "on_tool_end":
                    tool_name = event.get("name", "unknown")
                    tool_output = event.get("data", {}).get("output", "")
                    logger.info(f"✅ Tool completed: {tool_name}")
                    
                    yield {
                        "type": "tool_end",
                        "tool": tool_name,
                        "session_id": session_id
                    }
                    
                    # Start synthesis step and stream tool output
                    if current_step == "fetching" and tool_output:
                        import time
                        import asyncio
                        import json
                        
                        current_step = "synthesis"
                        step_start_time = time.time()
                        yield {
                            "type": "step_start",
                            "step": "synthesis",
                            "session_id": session_id
                        }
                        
                        # Try to parse JSON output (answer + sources)
                        try:
                            # First try to parse the tool_output as JSON
                            if isinstance(tool_output, str):
                                result = json.loads(tool_output)
                            else:
                                result = tool_output  # Already a dict
                                
                            # Extract answer and sources
                            answer_content = result.get("answer", {})
                            sources = result.get("sources", [])
                            
                            # Get the answer content and structured data
                            answer_content = result.get("answer", {})
                            structured_data = result.get("structured", {})
                            
                            # Check if we have a structured answer with sections
                            if isinstance(answer_content, dict) and "sections" in answer_content:
                                # The answer is already formatted by the tool, so we just use it directly.
                                ui_formatted = answer_content
                                
                                # Set the accumulated answer to the formatted UI structure
                                accumulated_answer = ui_formatted
                                
                                # Send the complete structured answer in one go
                                yield {
                                    "type": "complete_structured",
                                    "content": ui_formatted,
                                    "session_id": session_id
                                }
                            else:
                                # Legacy plain text format - stream character by character
                                answer_text = str(answer_content) if answer_content else str(result.get("answer", tool_output))
                                accumulated_answer = ""
                                
                                for char in answer_text:
                                    accumulated_answer += char
                                    yield {
                                        "type": "token",
                                        "content": char,
                                        "session_id": session_id
                                    }
                                    await asyncio.sleep(0.01)
                                    
                        except json.JSONDecodeError:
                            # Fallback if not JSON - treat as plain text
                            answer_text = str(tool_output)
                            sources = []
                            accumulated_answer = ""
                            
                            for char in answer_text:
                                accumulated_answer += char
                                yield {
                                    "type": "token",
                                    "content": char,
                                    "session_id": session_id
                                }
                                await asyncio.sleep(0.01)
                        
                        # Send sources as soon as available (before streaming answer)
                        if sources:
                            yield {
                                "type": "sources_ready",
                                "sources": sources,
                                "session_id": session_id
                            }
            
            # Send completion event with full answer and sources
            logger.info(f"✓ Streaming complete for thread_id: {thread_id}")
            
            # Handle structured vs string answers correctly
            if isinstance(accumulated_answer, dict):
                # For structured answers, send the object directly 
                # FastAPI will serialize it properly for JSON transmission
                completion_answer = accumulated_answer
            else:
                # For string answers, keep as string
                completion_answer = accumulated_answer
                
            yield {
                "type": "complete",
                "answer": completion_answer,
                "sources": sources,
                "session_id": session_id
            }
            
        except RuntimeError as e:
            logger.error(f"Checkpointer error during streaming: {e}")
            yield {
                "type": "error",
                "message": "Conversation persistence service unavailable",
                "session_id": session_id
            }
        except Exception as e:
            logger.error(f"Error during streaming: {e}", exc_info=True)
            yield {
                "type": "error",
                "message": str(e),
                "session_id": session_id
            }
