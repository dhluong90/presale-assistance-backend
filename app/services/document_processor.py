"""Document processor service for extracting text from PowerPoint files."""

import os
import logging
from typing import Dict, List, Optional, Any
import tempfile

import pandas as pd
import numpy as np
from pptx import Presentation

from app.config import settings
from app.services.sources import DocumentSource, LocalFileSource

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Service for processing PowerPoint documents from Google Drive."""
    
    def __init__(self, source: Optional[DocumentSource] = None):
        """Initialize the document processor.
        
        Args:
            source: Document source to use. Defaults to LocalFileSource if not provided.
        """
        self.source = source or LocalFileSource()
        self.data_dir = settings.DATA_DIR
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
    
    async def process_ppt_file(self, file_content: bytes) -> str:
        """Extract text content from a PowerPoint file."""
        try:
            # Create a temporary file to save the PPT content
            with tempfile.NamedTemporaryFile(suffix='.pptx', delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            # Extract text from the PPT file
            text_content = self._extract_text_from_ppt(temp_file_path)
            
            # Clean up the temporary file
            os.unlink(temp_file_path)
            
            return text_content
        except Exception as e:
            logger.error(f"Error processing PPT file: {str(e)}")
            raise
    
    def _extract_text_from_ppt(self, file_path: astr) -> str:
        """Extract text from a PowerPoint file."""
        presentation = Presentation(file_path)
        text_content = []
        
        # Extract slide titles and content
        for i, slide in enumerate(presentation.slides):
            slide_text = []
            
            # Get slide title if available
            if slide.shapes.title and slide.shapes.title.text:
                slide_text.append(f"Slide {i+1} - {slide.shapes.title.text}")
            else:
                slide_text.append(f"Slide {i+1}")
            
            # Extract text from all shapes in the slide
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text:
                    # Skip if this is the title we already added
                    if shape == slide.shapes.title:
                        continue
                    slide_text.append(shape.text)
            
            # Add slide content to overall content
            text_content.append("\n".join(slide_text))
        
        return "\n\n".join(text_content)
    
    async def process_all_files(self, source_path: Optional[str] = None) -> Dict[str, Dict]:
        """Process all PowerPoint files from the configured source.
        
        Args:
            source_path: Path or identifier for the source location (e.g., folder_id for Google Drive)
            
        Returns:
            Dictionary mapping filenames to their processed content and metadata
        """
        # List all files from the source
        files = await self.source.list_files(source_path)
        
        # Filter for PowerPoint files
        ppt_files = [f for f in files if f['mimeType'] == 'application/vnd.openxmlformats-officedocument.presentationml.presentation']
        
        results = {}
        for file in ppt_files:
            try:
                # Get the file from source
                file_name, file_content = await self.source.get_file(file['id'])
                
                # Process the file
                text_content = await self.process_ppt_file(file_content)
                
                # Store the result
                results[file_name] = {
                    'id': file['id'],
                    'name': file_name,
                    'content': text_content,
                    'metadata': {
                        'created': file.get('createdTime'),
                        'modified': file.get('modifiedTime')
                    }
                }
                
                logger.info(f"Successfully processed file: {file_name}")
            except Exception as e:
                logger.error(f"Error processing file {file.get('name')}: {str(e)}")
        
        return results