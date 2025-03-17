"""Main application entry point for the Presale Assistance API."""

import os
import logging
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any

from app.config import settings
from app.services.auth import get_current_user
from app.services.agent import PresaleAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Presale Assistance API",
    description="API for interacting with the Presale Assistant powered by Gemini and VertexAI",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class PromptRequest(BaseModel):
    prompt: str
    context: Optional[Dict[str, Any]] = None

# Response models
class AgentResponse(BaseModel):
    response: str
    sources: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None

# Initialize agent
presale_agent = PresaleAgent()

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Presale Assistance API is running"}

@app.post("/api/prompt", response_model=AgentResponse)
async def process_prompt(request: PromptRequest, current_user: Dict = Depends(get_current_user)):
    """Process a prompt using the presale assistant."""
    try:
        logger.info(f"Processing prompt request from user {current_user['email']}")
        response = await presale_agent.process_prompt(
            prompt=request.prompt,
            context=request.context,
            user=current_user
        )
        return response
    except Exception as e:
        logger.error(f"Error processing prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def get_status(current_user: Dict = Depends(get_current_user)):
    """Get the status of the presale assistant."""
    try:
        status = await presale_agent.get_status()
        return status
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)