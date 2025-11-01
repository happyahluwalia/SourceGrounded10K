#!/usr/bin/env python3
"""
This module defines the SupervisorAgent, the main entry point for the v2 agentic system.
"""

import logging
from typing import Literal
from pathlib import Path
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_ollama import ChatOllama

from app.core.config import settings
from app.tools.filing_qa_tool import answer_filing_question

logger = logging.getLogger(__name__)

class SupervisorAgent:
    """
    The main Supervisor agent that orchestrates all other tools and agents.
    For now, its only tool is the comprehensive FilingQATool.
    """
    def __init__(self):
        self.model_name = settings.supervisor_model
        self.tools = [answer_filing_question]
        self.tools_by_name = {tool.name: tool for tool in self.tools}

        self.llm = ChatOllama(
            model=self.model_name,
            base_url=settings.ollama_base_url,
            temperature=0.1
        )
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.graph = self._build_graph()

    def _build_graph(self):
        """Builds the LangGraph state machine for the supervisor."""
        
        def llm_call(state: MessagesState):
            """The supervisor LLM decides which tool to call."""
            try:
                prompt_path = Path(__file__).parent.parent / "prompts" / "supervisor.txt"
                system_prompt = prompt_path.read_text()
            except FileNotFoundError:
                logger.error(f"Supervisor prompt file not found at {Path(__file__).parent.parent / 'prompts' / 'supervisor.txt'}")
                system_prompt = "You are a helpful assistant. Use the tools available to answer the user's question."

            messages = [SystemMessage(content=system_prompt)] + state["messages"]
            response = self.llm_with_tools.invoke(messages)
            return {"messages": [response]}

        def tool_node(state: MessagesState):
            """Executes the tool chosen by the supervisor."""
            result = []
            last_message = state["messages"][-1]
            for tool_call in last_message.tool_calls:
                tool = self.tools_by_name[tool_call["name"]]
                observation = tool.invoke(tool_call["args"])
                result.append(ToolMessage(content=str(observation), tool_call_id=tool_call["id"]))
            return {"messages": result}

        def should_continue(state: MessagesState) -> Literal["tool_node", END]:
            """Routes to tool execution or ends the process."""
            return "tool_node" if state["messages"][-1].tool_calls else END

        graph_builder = StateGraph(MessagesState)
        graph_builder.add_node("supervisor_llm", llm_call)
        graph_builder.add_node("specialist_tool", tool_node)
        graph_builder.add_edge(START, "supervisor_llm")
        graph_builder.add_conditional_edges(
            "supervisor_llm",
            should_continue,
            {"tool_node": "specialist_tool", END: END}
        )
        # After the tool runs, the process ends. The tool itself provides the final answer.
        graph_builder.add_edge("specialist_tool", END)
        
        return graph_builder.compile()

    def invoke(self, query: str) -> dict:
        """Processes a query synchronously."""
        messages = [HumanMessage(content=query)]
        result = self.graph.invoke({"messages": messages})
        
        # The final answer is the content of the ToolMessage from the specialist tool
        final_answer = "Could not process the request."
        for msg in reversed(result['messages']):
            if isinstance(msg, ToolMessage):
                final_answer = msg.content
                break

        return {
            "query": query,
            "answer": final_answer,
            "messages": result['messages']
        }

    async def ainvoke(self, query: str) -> dict:
        """Processes a query asynchronously."""
        messages = [HumanMessage(content=query)]
        result = await self.graph.ainvoke({"messages": messages})
        
        # The final answer is the content of the ToolMessage from the specialist tool
        final_answer = "Could not process the request."
        for msg in reversed(result['messages']):
            if isinstance(msg, ToolMessage):
                final_answer = msg.content
                break

        return {
            "query": query,
            "answer": final_answer,
            "messages": result['messages']
        }
