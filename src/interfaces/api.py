# API mode: http://localhost:8000/docs
from fastapi import FastAPI, HTTPException, Depends, Security, Request
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import List
from core.mcp_server import MCPServer
from utils.config import config
from utils.mcp_schema import MCPInferenceRequest, MCPInferenceResponse, MCPModelInfo, MCPContext
import logging
from starlette.status import HTTP_403_FORBIDDEN, HTTP_429_TOO_MANY_REQUESTS
import time
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Fintech AI Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # Explicitly allow OPTIONS
    allow_headers=["*"],
    expose_headers=["*"]
)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Add the missing get_mcp dependency
async def get_mcp() -> MCPServer:
    """Dependency to get MCP server instance"""
    from main import setup_mcp  # Local import to avoid circular dependency
    return await setup_mcp()

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key is None:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Missing API key"
        )
    if api_key != config.api_key:  # Compare with configured API key
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Invalid API key"
        )
    return api_key

class QueryRequest(BaseModel):
    query: str
    use_web_fallback: bool = False

class Source(BaseModel):
    title: str
    relevance: float
    type: str

class QueryResponse(BaseModel):
    response: str
    sources: List[Source]
    is_from_web: bool

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests = {}
        self.rate_limit = requests_per_minute
        self.window = 60  # 1 minute window
    
    async def check(self, client_id: str) -> bool:
        now = time.time()
        client_requests = self.requests.get(client_id, [])
        
        # Remove old requests
        client_requests = [t for t in client_requests if now - t < self.window]
        
        if len(client_requests) >= self.rate_limit:
            return False
        
        client_requests.append(now)
        self.requests[client_id] = client_requests
        return True

rate_limiter = RateLimiter()

@app.options("/query")
async def query_options():
    return {}  # Handle OPTIONS request

@app.post("/query")
async def query_agent(
    request: QueryRequest, 
    api_key: str = Depends(get_api_key),
    mcp: MCPServer = Depends(get_mcp)
):
    # Rate limiting check
    if not await rate_limiter.check(api_key):
        raise HTTPException(
            status_code=HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    
    try:
        # Try vector store first
        results = await mcp.execute_tool("query_vector_store", request.query)
        
        # Get context from vector store if available
        context = None
        if results:
            context = await mcp.execute_tool("format_response", request.query, results)
        
        # Generate LLM response with context
        response = await mcp.execute_tool(
            "generate_response",
            request.query,
            context
        )
        
        # Clean up response and format for API
        return QueryResponse(
            response=response,
            sources=[{
                'title': r['metadata'].get('source', 'Unknown'),
                'relevance': round((1 - r.get('distance', 0)) * 100, 2),
                'type': r['metadata'].get('type', 'unknown')
            } for r in results] if results else [],
            is_from_web=False
        )
        
    except Exception as e:
        logging.error(f"API query error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index")
async def index_documents(
    mcp: MCPServer = Depends(get_mcp),
    path: str = "data"
):
    try:
        docs = await mcp.execute_tool("process_documents", path)
        if not docs:
            return {"status": "error", "message": "No documents processed"}
        
        success = await mcp.execute_tool("index_documents", docs)
        return {
            "status": "success" if success else "error",
            "documents_processed": len(docs)
        }
    except Exception as e:
        logging.error(f"Document indexing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/infer", response_model=MCPInferenceResponse)
async def mcp_infer(
    mcp_request: MCPInferenceRequest,
    api_key: str = Depends(get_api_key),
    mcp: MCPServer = Depends(get_mcp)
):
    try:
        # Combine all context content for LLM
        context_str = " ".join([ctx.content for ctx in mcp_request.context])
        prompt = mcp_request.prompt

        # Generate response using LLM with context
        response = await mcp.execute_tool(
            "generate_response",
            prompt,
            context_str
        )

        # Build MCPModelInfo from config
        model_info = MCPModelInfo(
            model_id=mcp_request.model.model_id,
            provider=mcp_request.model.provider,
            version=mcp_request.model.version,
            parameters=mcp_request.model.parameters
        )

        return MCPInferenceResponse(
            request_id=mcp_request.request_id,
            model=model_info,
            context=mcp_request.context,
            prompt=prompt,
            response=response,
            sources=None
        )
    except Exception as e:
        return MCPInferenceResponse(
            request_id=mcp_request.request_id,
            model=mcp_request.model,
            context=mcp_request.context,
            prompt=mcp_request.prompt,
            response="",
            error=str(e)
        )