import boto3
import logging
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional, Tuple
import os
from app.core.config import settings

logger = logging.getLogger(__name__)

class S3Service:
    """AWS S3 service for file upload and management."""
    
    def __init__(self):
        """Initialize S3 client with credentials from settings."""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            self.bucket_name = settings.AWS_S3_BUCKET_NAME
            logger.info(f"S3 client initialized for bucket: {self.bucket_name}")
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise
        except Exception as e:
            logger.error(f"Error initializing S3 client: {e}")
            raise
    
    def upload_file(self, file_content: bytes, file_key: str, content_type: str = 'application/pdf') -> bool:
        """
        Upload file content to S3 bucket.
        
        Args:
            file_content: File content as bytes
            file_key: S3 key (filename) for the uploaded file
            content_type: MIME type of the file
            
        Returns:
            bool: True if upload successful, False otherwise
        """
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=file_content,
                ContentType=content_type
            )
            logger.info(f"File uploaded successfully to S3: {file_key}")
            return True
        except ClientError as e:
            logger.error(f"Error uploading file to S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error uploading file to S3: {e}")
            return False
    
    def download_file(self, file_key: str) -> Optional[bytes]:
        """
        Download file content from S3 bucket.
        
        Args:
            file_key: S3 key (filename) of the file to download
            
        Returns:
            bytes: File content if successful, None otherwise
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_key)
            file_content = response['Body'].read()
            logger.info(f"File downloaded successfully from S3: {file_key}")
            return file_content
        except ClientError as e:
            logger.error(f"Error downloading file from S3: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading file from S3: {e}")
            return None
    
    def delete_file(self, file_key: str) -> bool:
        """
        Delete file from S3 bucket.
        
        Args:
            file_key: S3 key (filename) of the file to delete
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)
            logger.info(f"File deleted successfully from S3: {file_key}")
            return True
        except ClientError as e:
            logger.error(f"Error deleting file from S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting file from S3: {e}")
            return False
    
    def file_exists(self, file_key: str) -> bool:
        """
        Check if file exists in S3 bucket.
        
        Args:
            file_key: S3 key (filename) to check
            
        Returns:
            bool: True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=file_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            logger.error(f"Error checking file existence in S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking file existence in S3: {e}")
            return False
    
    def get_file_url(self, file_key: str, expires_in: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for file access.
        
        Args:
            file_key: S3 key (filename)
            expires_in: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            str: Presigned URL if successful, None otherwise
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': file_key},
                ExpiresIn=expires_in
            )
            logger.info(f"Presigned URL generated for file: {file_key}")
            return url
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error generating presigned URL: {e}")
            return None

# Global S3 service instance
s3_service = None

def get_s3_service() -> Optional[S3Service]:
    """
    Get S3 service instance (lazy initialization).
    
    Returns:
        S3Service: S3 service instance or None if not configured
    """
    global s3_service
    
    if s3_service is None:
        try:
            # Only initialize if S3 credentials are available
            if (settings.AWS_ACCESS_KEY_ID and 
                settings.AWS_SECRET_ACCESS_KEY and 
                settings.AWS_S3_BUCKET_NAME):
                s3_service = S3Service()
            else:
                logger.warning("S3 credentials not configured, S3 service unavailable")
                return None
        except Exception as e:
            logger.error(f"Failed to initialize S3 service: {e}")
            return None
    
    return s3_service