"""
FastAPI application for the Agentic Research & Brief Generator.

This module provides the main FastAPI application that exposes the agent's
functionality as a REST API.
"""
import logging
import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from core.types import APIRequest, APIResponse
from agents.orchestrator import Orchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Agentic Research & Brief Generator",
    description="API for generating research briefs using agentic design patterns",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator instance
_orchestrator = None

class RunRequest(BaseModel):
    """Request model for the /run endpoint."""
    query: str
    max_workers: Optional[int] = 3
    timeout: Optional[int] = 30

@app.on_event("startup")
async def startup_event():
    """Initialize the orchestrator when the application starts."""
    global _orchestrator
    logger.info("Initializing orchestrator...")
    _orchestrator = Orchestrator()
    logger.info("Orchestrator initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources when the application shuts down."""
    global _orchestrator
    if _orchestrator:
        logger.info("Shutting down orchestrator...")
        await _orchestrator.close()
        _orchestrator = None
        logger.info("Orchestrator shut down")

async def get_orchestrator() -> Orchestrator:
    """Dependency to get the orchestrator instance."""
    if _orchestrator is None:
        raise HTTPException(
            status_code=500,
            detail="Orchestrator not initialized"
        )
    return _orchestrator

@app.post("/run", response_model=APIResponse, tags=["API"])
async def run(
    request: RunRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator)
) -> APIResponse:
    """
    Process a research query and generate a brief.
    
    This endpoint accepts a natural language query and returns a structured
    research brief with relevant information and references.
    
    Args:
        request: The run request containing the query and optional parameters
        
    Returns:
        APIResponse with the generated brief or an error message
    """
    try:
        logger.info(f"Processing query: {request.query}")
        
        # Create API request
        api_request = APIRequest(
            query=request.query,
            metadata={
                "max_workers": request.max_workers,
                "timeout": request.timeout
            }
        )
        
        # Process the request
        response = await orchestrator.process_request(api_request)
        
        if not response.success:
            logger.error(f"Failed to process query: {response.error}")
            raise HTTPException(
                status_code=400,
                detail=response.error or "Failed to process query"
            )
        
        logger.info(f"Successfully processed query: {request.query}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0"
    }

def start():
    """Start the FastAPI server with uvicorn."""
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    start()
