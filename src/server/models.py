from typing import Any, Dict, Optional, Union
from pydantic import BaseModel

class PipelineRequest(BaseModel):
    instruction: str
    # either a raw JSON-string or a dict
    input: Union[str, Dict[str, Any]]
    

class PipelineRequest(BaseModel):
    instruction: str
    input: Union[str, Dict[str, Any]]
    output: Optional[str] = None   # ← добавили

    class Config:
        extra = "forbid"  # запрещаем всё прочее

class AnalyzeResp(BaseModel):
    analysis: Dict[str, Any]
    hash: str
    