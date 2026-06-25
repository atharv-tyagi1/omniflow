from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class WorkflowNodeSchema(BaseModel):
    id: str
    type: str
    position_x: float = 0.0
    position_y: float = 0.0
    config: Dict[str, Any] = Field(default_factory=dict)

class WorkflowEdgeSchema(BaseModel):
    id: str
    source: str
    target: str
    source_handle: Optional[str] = None
    target_handle: Optional[str] = None

class WorkflowDraftUpdate(BaseModel):
    nodes: List[WorkflowNodeSchema]
    edges: List[WorkflowEdgeSchema]

class WorkflowPublishResponse(BaseModel):
    version_id: str
    version_number: int
