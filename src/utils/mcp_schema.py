from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class MCPContext(BaseModel):
    context_id: str
    context_type: str = "document"
    content: str
    metadata: Dict[str, Any] = {}

class MCPModelInfo(BaseModel):
    model_id: str
    provider: str
    version: str
    parameters: Dict[str, Any] = {}

class MCPInferenceRequest(BaseModel):
    request_id: str
    model: MCPModelInfo
    context: List[MCPContext]
    prompt: str

class MCPInferenceResponse(BaseModel):
    request_id: str
    model: MCPModelInfo
    context: List[MCPContext]
    prompt: str
    response: str
    sources: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

class MCPVersion(BaseModel):
    version: str = "1.0.0"
    protocol: str = "mcp"

class MCPContextValidator:
    @staticmethod
    def validate_context(context: MCPContext) -> bool:
        # Add validation logic
        pass

class MCPStreamResponse(MCPInferenceResponse):
    is_streaming: bool = True
    chunk_id: Optional[int] = None