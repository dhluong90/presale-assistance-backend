"""Google Drive implementation of document source."""

import io
import logging
from typing import Dict, List, Optional, Any, Tuple

from googleapiclient.http import MediaIoBaseDownload

from app.config import settings
from app.services.auth import get_google_drive_service
from .base import DocumentSource

logger = logging.getLogger(__name__)

class GoogleDriveSource:
    """Google Drive implementation of DocumentSource."""
    
    def __init__(self):
        self.drive_service = None
    
    def _init_drive_service(self):
        if not self.drive_service:
            self.drive_service = get_google_drive_service()
    
    async def list_files(self, folder_id: Optional[str] = None) -> List[Dict]:
        self._init_drive_service()
        
        if not folder_id:
            folder_id = settings.GOOGLE_DRIVE_FOLDER_ID
        
        try:
            query = f"'{folder_id}' in parents and trashed = false"
            fields = "files(id, name, mimeType, createdTime, modifiedTime)"
            
            response = self.drive_service.files().list(
                q=query,
                spaces='drive',
                fields=fields
            ).execute()
            
            return response.get('files', [])
        except Exception as e:
            logger.error(f"Error listing Drive files: {str(e)}")
            raise
    
    async def get_file(self, file_id: str) -> Tuple[str, bytes]:
        self._init_drive_service()
        
        try:
            # Get file metadata
            file_metadata = self.drive_service.files().get(fileId=file_id).execute()
            file_name = file_metadata['name']
            
            # Download file content
            request = self.drive_service.files().get_media(fileId=file_id)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            return file_name, file_content.getvalue()
        except Exception as e:
            logger.error(f"Error downloading file {file_id}: {str(e)}")
            raise