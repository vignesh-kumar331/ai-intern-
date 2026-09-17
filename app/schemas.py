from typing import Literal, Optional, Any
from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)

class QueryPlan(BaseModel):
    intent: Literal['count', 'aggregate', 'list']
    metric: Optional[Literal['count', 'avg_customer_rating', 'avg_resolution_time_hrs', 'avg_response_time_hrs', 'max_resolution_time_hrs', 'min_customer_rating']] = 'count'
    group_by: Optional[Literal['agent_id', 'category', 'priority', 'status']] = None
    category: Optional[Literal['Billing', 'Technical', 'General']] = None
    priority: Optional[Literal['Low', 'Medium', 'High', 'Critical']] = None
    status: Optional[Literal['Open', 'Resolved', 'Escalated']] = None
    unresolved_only: bool = False
    agent_id: Optional[str] = None
    time_range: Optional[Literal['this_week', 'this_month', 'last_7_days', 'last_30_days']] = None
    resolution_gt: Optional[float] = None
    resolution_lte: Optional[float] = None
    limit: int = Field(default=10, ge=1, le=100)
    sort_desc: bool = True

class QueryResponse(BaseModel):
    question: str
    answer: str
    plan: dict[str, Any]
    rows: list[dict[str, Any]] = []
    llm_used: bool

class HealthResponse(BaseModel):
    status: str
    rows: int
    llm_provider: str
    llm_model: str
    llm_available: bool
