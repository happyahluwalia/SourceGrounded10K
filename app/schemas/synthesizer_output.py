"""
Pydantic schemas for synthesizer structured output.
Used with Ollama's structured outputs feature to guarantee valid JSON.
"""
from typing import List, Dict, Optional, Any, Literal
from pydantic import BaseModel, Field


class Section(BaseModel):
    """A section in the answer."""
    type: Literal["paragraph", "table", "key_findings", "comparison_summary"] = Field(
        description="Type of section"
    )
    content: str = Field(description="Plain text content without formatting")
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="For tables: {'headers': [...], 'rows': [[...]]}}"
    )
    citations: List[int] = Field(
        default_factory=list,
        description="0-based indices of source documents"
    )


class Answer(BaseModel):
    """The answer containing sections."""
    sections: List[Section] = Field(description="List of answer sections")


class BusinessContext(BaseModel):
    """Business context for a company."""
    growth_drivers: str = Field(description="What drove the metrics")
    headwinds: str = Field(description="What held them back")
    explanation: str = Field(description="Why these numbers matter")
    citations: List[int] = Field(
        default_factory=list,
        description="0-based indices of source documents"
    )


class CompanyData(BaseModel):
    """Data for a single company."""
    key_findings: List[str] = Field(
        default_factory=list,
        description="List of key findings"
    )
    metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metrics dictionary"
    )
    context_source: Optional[str] = Field(
        default=None,
        description="Source of context (e.g., '10-K Item 7')"
    )
    business_context: Optional[BusinessContext] = Field(
        default=None,
        description="Business context explaining the metrics"
    )


class ComparisonDifference(BaseModel):
    """A difference between companies."""
    aspect: str = Field(description="Aspect being compared")
    description: str = Field(description="Description of the difference")


class Comparison(BaseModel):
    """Comparison data for multi-company queries."""
    summary: Optional[str] = Field(
        default=None,
        description="Plain text explaining key differences"
    )
    winner: Optional[str] = Field(
        default=None,
        description="Ticker of the winner or null"
    )
    metric: Optional[str] = Field(
        default=None,
        description="Metric used for comparison (e.g., 'revenue_growth')"
    )
    differences: List[ComparisonDifference] = Field(
        default_factory=list,
        description="List of differences between companies"
    )


class SynthesizerOutput(BaseModel):
    """Complete synthesizer output schema."""
    answer: Answer = Field(description="The answer with sections")
    companies: Dict[str, CompanyData] = Field(
        default_factory=dict,
        description="Company data keyed by ticker"
    )
    comparison: Optional[Comparison] = Field(
        default=None,
        description="Comparison data (null for single-company queries)"
    )
    visualization_hint: Optional[Literal["table", "bar_chart", "none"]] = Field(
        default="none",
        description="Suggested visualization type"
    )
    confidence: Literal["high", "medium", "low"] = Field(
        default="medium",
        description="Confidence level of the answer"
    )
    missing_data: List[str] = Field(
        default_factory=list,
        description="List of missing data points"
    )
