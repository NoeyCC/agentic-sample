from enum import Enum, auto
from typing import Dict, List, Optional, TypedDict, Union, Literal
from dataclasses import dataclass
from pydantic import BaseModel


class WorkerType(str, Enum):
    """Supported worker types."""
    WEB_SEARCH = "web_search"
    CODE_READ = "code_read"
    DATA_QUERY = "data_query"


class IntentType(str, Enum):
    """Supported intent types for routing."""
    RESEARCH = "research"
    CODE_ANALYSIS = "code_analysis"
    DATA_ANALYSIS = "data_analysis"


class WorkerResult(BaseModel):
    """Result from a worker's execution."""
    content: str
    metadata: Dict[str, Union[str, int, float, bool, None]] = {}
    source: str


class EvaluationResult(BaseModel):
    """Result from evaluator."""
    is_complete: bool
    feedback: str
    score: float  # 0.0 to 1.0


class ExecutionPlan(BaseModel):
    """Plan for executing a query."""
    query: str
    required_workers: List[WorkerType]
    context: Dict[str, str] = {}


class BriefOutput(BaseModel):
    """Final brief output format."""
    title: str
    content: str
    references: List[Dict[str, str]]
    generated_at: str


class WebSearchResult(TypedDict):
    """Structure for web search results."""
    title: str
    url: str
    snippet: str
    source: str


@dataclass
class WorkerResponse:
    """Response from a worker."""
    success: bool
    result: Optional[WorkerResult] = None
    error: Optional[str] = None


class APIRequest(BaseModel):
    """Request model for the API endpoint."""
    query: str


class APIResponse(BaseModel):
    """Response model for the API endpoint."""
    success: bool
    brief: Optional[BriefOutput] = None
    error: Optional[str] = None
