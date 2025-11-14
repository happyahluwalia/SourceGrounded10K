"""
Pydantic schemas for planner structured output.
Used with Ollama's structured outputs feature to guarantee valid JSON.
"""
from typing import List, Literal
from pydantic import BaseModel, Field


class Task(BaseModel):
    """A single task in the execution plan."""
    ticker: str = Field(description="Company ticker symbol (e.g., 'AAPL', 'MSFT')")
    filing_type: Literal["10-K", "10-Q"] = Field(
        default="10-K",
        description="SEC filing type"
    )
    search_query: str = Field(
        description="Precise query for vector search using official terms"
    )
    timeframe: Literal["latest_annual", "latest_quarter"] = Field(
        default="latest_annual",
        description="Timeframe for the data"
    )


class PlannerOutput(BaseModel):
    """Complete planner output schema."""
    intent: Literal["find_data", "compare_data"] = Field(
        description="User's goal: find_data for single company, compare_data for multiple"
    )
    tasks: List[Task] = Field(
        description="List of tasks to execute. For comparison queries, include one task per company."
    )
