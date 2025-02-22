from pydantic import BaseModel
from typing import Optional, Any, Dict


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SuccessResponse(BaseModel):
    message: str
    data: Optional[Dict[str, Any]] = None
