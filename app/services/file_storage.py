import os
import shutil
import logging
from typing import Optional, Tuple, BinaryIO
from fastapi import UploadFile
from app.core.config import settings
from app.services.s3_service import get_s3_service

logger = logging.getLogger(__name__)

class FileStorageService:
    """Unified file storage service that can use local storage or S3."""
    
    def __init__(self):
        self.storage_mode = settings.FILE_STORAGE_MODE
        self.s3_service = get_s3_service() if self.storage_mode == 's3' else None
        logger.info(f"FileStorageService initialized with mode: {self.storage_mode}")
    
    async def save_file(self, file: UploadFile, filename: str) -> Tuple[bool, str]:
        """
        Save uploaded file to storage (local or S3).
        
        Args:
            file: FastAPI UploadFile object
            filename: Name to save the file as
            
        Returns:
            Tuple[bool, str]: (success, file_path_or_key)
        """
        try:
            # Read file content
            file_content = await file.read()
            await file.seek(0)  # Reset file pointer
            
            if self.storage_mode == 's3' and self.s3_service:
                # Upload to S3
                success = self.s3_service.upload_file(
                    file_content=file_content,
                    file_key=filename,
                    content_type=file.content_type or 'application/pdf'
                )
                if success:
                    logger.info(f"File saved to S3: {filename}")
                    return True, f"s3://{settings.AWS_S3_BUCKET_NAME}/{filename}"
                else:
                    logger.error(f"Failed to save file to S3: {filename}")
                    return False, ""
            else:
                # Save to local storage
                os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
                file_path = os.path.join(settings.UPLOAD_FOLDER, filename)
                
                with open(file_path, "wb") as buffer:
                    buffer.write(file_content)
                
                logger.info(f"File saved locally: {file_path}")
                return True, file_path
                
        except Exception as e:
            logger.error(f"Error saving file {filename}: {e}")
            return False, ""
    
    def read_file(self, file_path_or_key: str) -> Optional[bytes]:
        """
        Read file content from storage.
        
        Args:
            file_path_or_key: File path (local) or S3 key
            
        Returns:
            bytes: File content or None if error
        """
        try:
            if file_path_or_key.startswith('s3://') and self.s3_service:
                # Extract S3 key from S3 URL
                s3_key = file_path_or_key.split('/', 3)[-1]  # Remove s3://bucket/
                return self.s3_service.download_file(s3_key)
            else:
                # Read from local storage
                if os.path.exists(file_path_or_key):
                    with open(file_path_or_key, 'rb') as f:
                        return f.read()
                else:
                    logger.warning(f"Local file not found: {file_path_or_key}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error reading file {file_path_or_key}: {e}")
            return None
    
    def delete_file(self, file_path_or_key: str) -> bool:
        """
        Delete file from storage.
        
        Args:
            file_path_or_key: File path (local) or S3 key
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if file_path_or_key.startswith('s3://') and self.s3_service:
                # Extract S3 key from S3 URL
                s3_key = file_path_or_key.split('/', 3)[-1]  # Remove s3://bucket/
                return self.s3_service.delete_file(s3_key)
            else:
                # Delete from local storage
                if os.path.exists(file_path_or_key):
                    os.remove(file_path_or_key)
                    logger.info(f"Local file deleted: {file_path_or_key}")
                    return True
                else:
                    logger.warning(f"Local file not found for deletion: {file_path_or_key}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error deleting file {file_path_or_key}: {e}")
            return False
    
    def file_exists(self, file_path_or_key: str) -> bool:
        """
        Check if file exists in storage.
        
        Args:
            file_path_or_key: File path (local) or S3 key
            
        Returns:
            bool: True if file exists, False otherwise
        """
        try:
            if file_path_or_key.startswith('s3://') and self.s3_service:
                # Extract S3 key from S3 URL
                s3_key = file_path_or_key.split('/', 3)[-1]  # Remove s3://bucket/
                return self.s3_service.file_exists(s3_key)
            else:
                # Check local storage
                return os.path.exists(file_path_or_key)
                
        except Exception as e:
            logger.error(f"Error checking file existence {file_path_or_key}: {e}")
            return False
    
    def get_file_url(self, file_path_or_key: str, expires_in: int = 3600) -> Optional[str]:
        """
        Get accessible URL for file (for S3) or return local path.
        
        Args:
            file_path_or_key: File path (local) or S3 key
            expires_in: URL expiration time in seconds (for S3 only)
            
        Returns:
            str: URL or file path
        """
        try:
            if file_path_or_key.startswith('s3://') and self.s3_service:
                # Generate presigned URL for S3
                s3_key = file_path_or_key.split('/', 3)[-1]  # Remove s3://bucket/
                return self.s3_service.get_file_url(s3_key, expires_in)
            else:
                # Return local file path
                return file_path_or_key if os.path.exists(file_path_or_key) else None
                
        except Exception as e:
            logger.error(f"Error getting file URL {file_path_or_key}: {e}")
            return None

# Global file storage service instance
file_storage_service = FileStorageService()