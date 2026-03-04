"""
Azure Blob Storage helper module for storing jaguar images.
"""
import os
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient, ContentSettings
from typing import Optional, Tuple
import io
from datetime import datetime
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class AzureStorageManager:
    """Manager for Azure Blob Storage operations."""
    
    def __init__(
        self,
        connection_string: Optional[str] = None,
        container_name: str = "jaguar-images"
    ):
        """
        Initialize Azure Storage Manager.
        
        Args:
            connection_string: Azure Storage connection string
            container_name: Name of the blob container
        """
        self.connection_string = connection_string or os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.container_name = container_name
        self.blob_service_client = None
        self.container_client = None
        
        if self.connection_string:
            print(f"[DEBUG] Azure Storage: Connection string found, initializing...")
            self._initialize_client()
        else:
            print(f"[DEBUG] Azure Storage: No connection string, using local storage")
            logger.warning("Azure Storage connection string not provided. Using local storage.")
    
    def _initialize_client(self):
        """Initialize blob service and container clients."""
        try:
            print(f"[DEBUG] Azure Storage: Creating BlobServiceClient...")
            # Create client with network timeouts (connection_timeout and read_timeout)
            self.blob_service_client = BlobServiceClient.from_connection_string(
                self.connection_string,
                connection_timeout=30,  # 30 seconds to establish connection
                read_timeout=90  # 90 seconds to complete read operations
            )
            print(f"[DEBUG] Azure Storage: Getting container client...")
            self.container_client = self.blob_service_client.get_container_client(
                self.container_name
            )
            
            print(f"[DEBUG] Azure Storage: Checking if container exists...")
            # Create container if it doesn't exist (with timeout)
            try:
                if not self.container_client.exists(timeout=15):
                    print(f"[DEBUG] Azure Storage: Creating container...")
                    self.container_client.create_container(public_access="blob", timeout=15)
                    logger.info(f"Created container: {self.container_name}")
            except Exception as container_error:
                print(f"[DEBUG] Azure Storage: Container check/create error: {container_error}")
                # If container operations fail but client is valid, continue anyway
                logger.warning(f"Container check failed but continuing: {container_error}")
            
            logger.info(f"Azure Storage initialized: {self.container_name}")
            print(f"[DEBUG] Azure Storage: ✓ Initialization complete")
        except Exception as e:
            logger.error(f"Failed to initialize Azure Storage: {e}")
            print(f"[DEBUG] Azure Storage: ✗ Initialization failed - {type(e).__name__}: {e}")
            raise Exception(f"Azure Storage initialization failed: {e}")
    
    def is_available(self) -> bool:
        """Check if Azure Storage is available."""
        return self.container_client is not None
    
    def upload_image(
        self,
        image_bytes: bytes,
        jaguar_id: str,
        filename: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Upload an image to Azure Blob Storage.
        
        Args:
            image_bytes: Image file content as bytes
            jaguar_id: Unique jaguar identifier
            filename: Original filename (optional)
        
        Returns:
            Tuple of (success: bool, blob_url: Optional[str])
        """
        if not self.is_available():
            error_msg = "Azure Storage not available - client not initialized"
            logger.error(error_msg)
            print(f"[DEBUG] Azure: {error_msg}")
            raise Exception(error_msg)
        
        try:
            # Generate blob name with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ext = "jpg"
            if filename:
                ext = filename.split(".")[-1].lower() if "." in filename else "jpg"
            
            blob_name = f"{jaguar_id}/{timestamp}.{ext}"
            
            print(f"[DEBUG] Azure: Preparing blob {blob_name}...")
            print(f"[DEBUG] Azure: Image size: {len(image_bytes)} bytes ({len(image_bytes)/1024/1024:.2f} MB)")
            
            # Get blob client
            print(f"[DEBUG] Azure: Getting blob client...")
            blob_client = self.container_client.get_blob_client(blob_name)
            
            # Set content type
            content_settings = ContentSettings(content_type=f"image/{ext}")
            
            print(f"[DEBUG] Azure: Starting upload (timeout: 60s)...")
            # Upload with proper timeout (60 seconds for large files)
            blob_client.upload_blob(
                image_bytes,
                overwrite=True,
                content_settings=content_settings,
                timeout=60  # 60 seconds timeout for large images
            )
            print(f"[DEBUG] Azure: ✓ Upload complete!")
            
            # Get blob URL
            blob_url = blob_client.url
            logger.info(f"Uploaded image to Azure: {blob_name}")
            print(f"[DEBUG] Azure: Blob URL: {blob_url}")
            
            return True, blob_url
            
        except Exception as e:
            error_msg = f"Failed to upload to Azure Blob Storage: {type(e).__name__}: {e}"
            logger.error(error_msg)
            print(f"[DEBUG] Azure: ✗ {error_msg}")
            raise Exception(error_msg)
    
    def upload_multiple_images(
        self,
        images: list[Tuple[bytes, str]],
        jaguar_id: str
    ) -> list[Tuple[bool, Optional[str]]]:
        """
        Upload multiple images for a jaguar.
        
        Args:
            images: List of (image_bytes, filename) tuples
            jaguar_id: Unique jaguar identifier
        
        Returns:
            List of (success, blob_url) tuples
        """
        results = []
        for image_bytes, filename in images:
            result = self.upload_image(image_bytes, jaguar_id, filename)
            results.append(result)
        return results
    
    def delete_image(self, blob_url: str) -> bool:
        """
        Delete an image from Azure Blob Storage.
        
        Args:
            blob_url: Full URL of the blob
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            # Extract blob name from URL
            blob_name = blob_url.split(f"{self.container_name}/")[-1]
            if self.container_client is None:
                logger.error("Container client is not initialized.")
                return False
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.delete_blob()
            logger.info(f"Deleted image from Azure: {blob_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete image from Azure: {e}")
            return False
    
    def list_jaguar_images(self, jaguar_id: str) -> list[str]:
        """
        List all images for a specific jaguar.
        
        Args:
            jaguar_id: Unique jaguar identifier
        
        Returns:
            List of blob URLs
        """
        if not self.is_available():
            return []
        
        try:
            blob_list = self.container_client.list_blobs(
                name_starts_with=f"{jaguar_id}/"
            )
            urls = [
                f"{self.container_client.url}/{blob.name}"
                for blob in blob_list
            ]
            return urls
        except Exception as e:
            logger.error(f"Failed to list images: {e}")
            return []


# Global instance
storage_manager = None


def get_storage_manager() -> AzureStorageManager:
    """Get or create global storage manager instance."""
    global storage_manager
    if storage_manager is None:
        print("[DEBUG] Initializing Azure Storage Manager...")
        storage_manager = AzureStorageManager()
        if storage_manager.is_available():
            print("[DEBUG] ✓ Azure Storage is available and ready")
        else:
            print("[DEBUG] ⚠ Azure Storage is NOT available, using local storage")
    return storage_manager
