"""Local filesystem implementation of document source."""

import os
import logging
from typing import Dict, List, Tuple

from .base import DocumentSource

logger = logging.getLogger(__name__)

class LocalFileSource:
    """Local filesystem implementation of DocumentSource."""
    
    async def list_files(self, directory: str) -> List[Dict]:
        try:
            files = []
            for entry in os.scandir(directory):
                if entry.is_file():
                    stats = entry.stat()
                    files.append({
                        'id': entry.path,
                        'name': entry.name,
                        'mimeType': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                        'createdTime': stats.st_ctime,
                        'modifiedTime': stats.st_mtime
                    })
            return files
        except Exception as e:
            logger.error(f"Error listing local files: {str(e)}")
            raise
    
    async def get_file(self, file_path: str) -> Tuple[str, bytes]:
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            return os.path.basename(file_path), content
        except Exception as e:
            logger.error(f"Error reading local file {file_path}: {str(e)}")
            raise