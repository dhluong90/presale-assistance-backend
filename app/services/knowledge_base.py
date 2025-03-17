"""Knowledge base service for storing and retrieving processed documents."""

import os
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

import numpy as np
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel

from app.config import settings
from app.services.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

class Document:
    """Document class for storing processed document data."""
    
    def __init__(self, id: str, content: str, metadata: Dict[str, Any]):
        """Initialize a document.
        
        Args:
            id (str): Unique identifier for the document
            content (str): The text content of the document
            metadata (Dict[str, Any]): Additional metadata about the document
        """
        self.id = id
        self.content = content
        self.metadata = metadata
        self.embedding = None

class KnowledgeBase:
    """Knowledge base for storing and retrieving processed documents."""
    
    def __init__(self):
        """Initialize the knowledge base.
        
        Creates a new KnowledgeBase instance with empty documents dictionary,
        initializes document processor and sets up cache directory.
        """
        self.documents = {}
        self.embeddings = None
        self.embedding_model = None
        self.document_processor = DocumentProcessor()
        self.cache_dir = settings.CACHE_DIR
        self.index_file = os.path.join(self.cache_dir, "knowledge_index.json")
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
    
    async def is_initialized(self) -> bool:
        """Check if the knowledge base is initialized.
        
        Returns:
            bool: True if index file exists and documents are loaded, False otherwise
        """
        return os.path.exists(self.index_file) and len(self.documents) > 0
    
    async def initialize(self):
        """Initialize the knowledge base.
        
        Loads existing index if available, processes files from Google Drive,
        generates embeddings for documents and saves the updated index.
        
        Raises:
            Exception: If initialization fails
        """
        try:
            # Load existing index if available
            if os.path.exists(self.index_file):
                await self._load_index()
            
            # Process all files from Google Drive
            processed_files = await self.document_processor.process_all_files()
            
            # Add or update documents in the knowledge base
            for file_name, file_data in processed_files.items():
                doc_id = file_data['id']
                doc_content = file_data['content']
                doc_metadata = {
                    'title': file_name,
                    'source': 'google_drive',
                    'id': doc_id,
                    **file_data['metadata']
                }
                
                self.documents[doc_id] = Document(doc_id, doc_content, doc_metadata)
            
            # Generate embeddings for all documents
            await self._generate_embeddings()
            
            # Save the updated index
            await self._save_index()
            
            logger.info(f"Knowledge base initialized with {len(self.documents)} documents")
        except Exception as e:
            logger.error(f"Error initializing knowledge base: {str(e)}")
            raise
    
    async def _load_index(self):
        """Load the knowledge base index from disk.
        
        Loads document data and embeddings from the index file on disk.
        If loading fails, resets documents dictionary to empty.
        
        Raises:
            Exception: If loading index fails
        """
        try:
            with open(self.index_file, 'r') as f:
                index_data = json.load(f)
            
            # Load documents
            for doc_id, doc_data in index_data['documents'].items():
                self.documents[doc_id] = Document(
                    id=doc_id,
                    content=doc_data['content'],
                    metadata=doc_data['metadata']
                )
                if 'embedding' in doc_data:
                    self.documents[doc_id].embedding = np.array(doc_data['embedding'])
            
            logger.info(f"Loaded {len(self.documents)} documents from index")
        except Exception as e:
            logger.error(f"Error loading knowledge base index: {str(e)}")
            self.documents = {}
    
    async def _save_index(self):
        """Save the knowledge base index to disk.
        
        Saves current document data and embeddings to the index file.
        
        Raises:
            Exception: If saving index fails
        """
        try:
            index_data = {
                'last_updated': datetime.now().isoformat(),
                'documents': {}
            }
            
            # Save documents
            for doc_id, doc in self.documents.items():
                index_data['documents'][doc_id] = {
                    'content': doc.content,
                    'metadata': doc.metadata
                }
                if doc.embedding is not None:
                    index_data['documents'][doc_id]['embedding'] = doc.embedding.tolist()
            
            with open(self.index_file, 'w') as f:
                json.dump(index_data, f)
            
            logger.info(f"Saved {len(self.documents)} documents to index")
        except Exception as e:
            logger.error(f"Error saving knowledge base index: {str(e)}")
    
    async def _generate_embeddings(self):
        """Generate embeddings for all documents in the knowledge base.
        
        Initializes embedding model if needed and generates embeddings
        for documents that don't have them.
        
        Raises:
            Exception: If generating embeddings fails
        """
        try:
            # Initialize embedding model if not already initialized
            if not self.embedding_model:
                self.embedding_model = TextEmbeddingModel.from_pretrained("textembedding-gecko@latest")
            
            # Generate embeddings for documents that don't have them
            for doc_id, doc in self.documents.items():
                if doc.embedding is None:
                    embedding = self.embedding_model.get_embeddings([doc.content])[0].values
                    doc.embedding = np.array(embedding)
            
            logger.info(f"Generated embeddings for {len(self.documents)} documents")
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    async def search(self, query: str, top_k: int = 3) -> List[Document]:
        """Search for relevant documents based on the query.
        
        Args:
            query (str): The search query text
            top_k (int, optional): Number of most relevant documents to return. Defaults to 3.
            
        Returns:
            List[Document]: List of top-k most relevant documents
            
        Raises:
            Exception: If search fails
        """
        try:
            # Initialize embedding model if not already initialized
            if not self.embedding_model:
                self.embedding_model = TextEmbeddingModel.from_pretrained("textembedding-gecko@latest")
            
            # Generate embedding for the query
            query_embedding = np.array(self.embedding_model.get_embeddings([query])[0].values)
            
            # Calculate similarity scores
            scores = {}
            for doc_id, doc in self.documents.items():
                if doc.embedding is not None:
                    # Calculate cosine similarity
                    similarity = np.dot(query_embedding, doc.embedding) / \
                                (np.linalg.norm(query_embedding) * np.linalg.norm(doc.embedding))
                    scores[doc_id] = similarity
            
            # Sort documents by similarity score
            sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            
            # Return top-k documents
            return [self.documents[doc_id] for doc_id, _ in sorted_docs[:top_k]]
        except Exception as e:
            logger.error(f"Error searching knowledge base: {str(e)}")
            return []