"""Base protocol for document sources."""

from typing import Dict, List, Optional, Any, Tuple, Protocol, runtime_checkable

@runtime_checkable
class DocumentSource(Protocol):
    """Protocol defining the interface for document sources."""
    
    async def list_files(self, source_path: str) -> List[Dict[str, Any]]:
        """List available files from the source.
        
        Args:
            source_path: Path or identifier for the source location
            
        Returns:
            List of file metadata dictionaries
        """
        ...
    
    async def get_file(self, file_id: str) -> Tuple[str, bytes]:
        """Retrieve a specific file from the source.
        
        Args:
            file_id: Identifier for the file
            
        Returns:
            Tuple of (filename, file_content)
        """
        ...