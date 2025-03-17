"""Presale Agent service using Gemini and VertexAI."""

import os
import logging
from typing import Dict, List, Optional, Any
import asyncio

from google.cloud import aiplatform
from vertexai.preview.generative_models import GenerativeModel, ChatSession

from app.config import settings
from app.services.document_processor import DocumentProcessor
from app.services.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)

class PresaleAgent:
    """Agent for handling presale assistance using Gemini and VertexAI."""
    
    def __init__(self):
        """Initialize the presale agent."""
        # Initialize Google Cloud services
        self._init_vertex_ai()
        
        # Initialize document processor
        self.document_processor = DocumentProcessor()
        
        # Initialize knowledge base
        self.knowledge_base = KnowledgeBase()
        
        # Initialize Gemini model
        self.model = GenerativeModel(settings.GEMINI_MODEL_ID)
        
        # Agent state
        self.is_ready = False
        self.last_sync = None
        
        # Start background initialization
        asyncio.create_task(self._initialize_agent())
    
    def _init_vertex_ai(self):
        """Initialize VertexAI client."""
        try:
            aiplatform.init(
                project=settings.GOOGLE_CLOUD_PROJECT,
                location=settings.VERTEX_LOCATION,
            )
            logger.info("VertexAI initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing VertexAI: {str(e)}")
            raise
    
    async def _initialize_agent(self):
        """Initialize the agent in the background."""
        try:
            # Check if knowledge base exists and is up to date
            if not await self.knowledge_base.is_initialized():
                logger.info("Knowledge base not initialized, starting initialization")
                await self.knowledge_base.initialize()
            
            # Mark agent as ready
            self.is_ready = True
            logger.info("Agent initialization complete")
        except Exception as e:
            logger.error(f"Error initializing agent: {str(e)}")
            self.is_ready = False
    
    async def process_prompt(self, prompt: str, context: Optional[Dict[str, Any]] = None, user: Optional[Dict] = None) -> Dict:
        """Process a prompt using the Gemini model and knowledge base."""
        if not self.is_ready:
            logger.warning("Agent not ready, initializing...")
            await self._initialize_agent()
            if not self.is_ready:
                raise Exception("Agent initialization failed")
        
        try:
            # Get relevant documents from knowledge base
            relevant_docs = await self.knowledge_base.search(prompt)
            
            # Create context for the model
            model_context = self._create_model_context(prompt, relevant_docs, context)
            
            # Generate response using Gemini
            response = await self._generate_response(model_context)
            
            # Format and return the response
            return {
                "response": response,
                "sources": [doc.metadata for doc in relevant_docs],
                "metadata": {
                    "model": settings.GEMINI_MODEL_ID,
                    "timestamp": str(self.last_sync)
                }
            }
        except Exception as e:
            logger.error(f"Error processing prompt: {str(e)}")
            raise
    
    def _create_model_context(self, prompt: str, relevant_docs: List, user_context: Optional[Dict] = None) -> str:
        """Create context for the model from relevant documents and user context."""
        context_parts = []
        
        # Add document context
        if relevant_docs:
            context_parts.append("Based on the following company information:")
            for i, doc in enumerate(relevant_docs):
                context_parts.append(f"[Document {i+1}] {doc.metadata.get('title', 'Untitled')}")
                context_parts.append(doc.content)
        
        # Add user context if provided
        if user_context:
            context_parts.append("Additional context:")
            for key, value in user_context.items():
                context_parts.append(f"{key}: {value}")
        
        # Add the prompt
        context_parts.append("\nUser prompt:")
        context_parts.append(prompt)
        
        return "\n".join(context_parts)
    
    async def _generate_response(self, context: str) -> str:
        """Generate a response using the Gemini model."""
        try:
            # Create a chat session
            chat = self.model.start_chat()
            
            # Generate response
            response = await chat.send_message_async(
                context,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 1024,
                }
            )
            
            return response.text
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise
    
    async def get_status(self) -> Dict[str, Any]:
        """Get the current status of the presale agent."""
        try:
            kb_status = await self.knowledge_base.get_status()
            
            return {
                "status": "ready" if self.is_ready else "initializing",
                "last_sync": str(self.last_sync) if self.last_sync else None,
                "knowledge_base": kb_status,
                "model": settings.GEMINI_MODEL_ID
            }
        except Exception as e:
            logger.error(f"Error getting agent status: {str(e)}")
            raise