"""
File Upload Service for Supabase Storage
Uploads product images to Supabase storage bucket with hash-based naming
"""
import os
import hashlib
from pathlib import Path
from typing import Optional
import httpx

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Warning: 'supabase' not installed. File upload to Supabase will be disabled.")

from config import settings


class FileUploadService:
    """Service for uploading files to Supabase storage"""
    
    def __init__(self):
        if not SUPABASE_AVAILABLE:
            self.enabled = False
            print("[FileUpload] Supabase upload disabled - supabase package not installed")
            return
        
        # Get Supabase credentials from settings or environment
        supabase_url = getattr(settings, 'SUPABASE_URL', None) or os.getenv('SUPABASE_URL')
        supabase_key = getattr(settings, 'SUPABASE_KEY', None) or os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            self.enabled = False
            print("[FileUpload] Supabase upload disabled - SUPABASE_URL or SUPABASE_KEY not set")
            return
        
        self.enabled = True
        self.bucket_name = 'images'
        self.upload_path_prefix = 'uploads'
        
        # Initialize Supabase client
        self.supabase: Client = create_client(supabase_url, supabase_key)
        print("[FileUpload] Supabase client initialized")
    
    @staticmethod
    def generate_file_hash(file_path: str) -> str:
        """Generate SHA256 hash of file content"""
        with open(file_path, 'rb') as f:
            file_content = f.read()
            return hashlib.sha256(file_content).hexdigest()
    
    @staticmethod
    def generate_file_hash_from_bytes(file_content: bytes) -> str:
        """Generate SHA256 hash from file bytes"""
        return hashlib.sha256(file_content).hexdigest()
    
    async def upload_file_from_path(self, file_path: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Upload a file from local filesystem to Supabase storage
        
        Args:
            file_path: Local file path
            filename: Optional filename (if not provided, uses file_path name)
        
        Returns:
            Public URL of uploaded file, or None if failed
        """
        if not self.enabled:
            print("[FileUpload] Upload disabled")
            return None
        
        try:
            # Read file content
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Generate hash and determine extension
            file_hash = self.generate_file_hash_from_bytes(file_content)
            file_extension = Path(file_path).suffix
            if not file_extension:
                file_extension = Path(filename).suffix if filename else '.jpg'
            
            upload_path = f"{self.upload_path_prefix}/{file_hash}{file_extension}"
            
            # Check if file already exists (deduplication)
            try:
                existing_files = self.supabase.storage.from_(self.bucket_name).list(
                    self.upload_path_prefix
                )
                
                # Search for file with same hash
                if existing_files:
                    for file_info in existing_files:
                        if file_info.get('name') == f"{file_hash}{file_extension}":
                            # File exists, return public URL
                            public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(upload_path)
                            print(f"[FileUpload] File already exists, reusing: {public_url}")
                            return public_url
            except Exception as e:
                # If list fails, continue with upload
                print(f"[FileUpload] Could not check for existing file: {e}")
            
            # Upload file
            try:
                result = self.supabase.storage.from_(self.bucket_name).upload(
                    upload_path,
                    file_content,
                    file_options={"content-type": "image/*"}
                )
                
                if result:
                    # Get public URL
                    public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(upload_path)
                    print(f"[FileUpload] Uploaded {filename or file_path} to {public_url}")
                    return public_url
                else:
                    print(f"[FileUpload] Upload failed for {filename or file_path}")
                    return None
            except Exception as upload_error:
                # Handle 409 Duplicate error - file already exists
                error_str = str(upload_error)
                if "409" in error_str or "Duplicate" in error_str or "already exists" in error_str.lower():
                    # File already exists, return existing public URL
                    public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(upload_path)
                    print(f"[FileUpload] File already exists, reusing: {public_url}")
                    return public_url
                else:
                    # Re-raise other errors
                    raise upload_error
                
        except Exception as e:
            print(f"[FileUpload] Error uploading {filename or file_path}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def upload_file_from_url(self, url: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Download file from URL and upload to Supabase storage
        
        Args:
            url: URL to download file from
            filename: Optional filename
        
        Returns:
            Public URL of uploaded file, or None if failed
        """
        if not self.enabled:
            print("[FileUpload] Upload disabled")
            return None
        
        try:
            # Download file from URL
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                file_content = response.content
            
            # Generate hash and determine extension
            file_hash = self.generate_file_hash_from_bytes(file_content)
            file_extension = Path(filename).suffix if filename else Path(url).suffix or '.jpg'
            
            upload_path = f"{self.upload_path_prefix}/{file_hash}{file_extension}"
            
            # Check if file already exists
            try:
                existing_files = self.supabase.storage.from_(self.bucket_name).list(
                    self.upload_path_prefix
                )
                
                # Search for file with same hash
                if existing_files:
                    for file_info in existing_files:
                        if file_info.get('name') == f"{file_hash}{file_extension}":
                            public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(upload_path)
                            print(f"[FileUpload] File already exists, reusing: {public_url}")
                            return public_url
            except Exception:
                pass
            
            # Upload file
            try:
                result = self.supabase.storage.from_(self.bucket_name).upload(
                    upload_path,
                    file_content,
                    file_options={"content-type": "image/*"}
                )
                
                if result:
                    public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(upload_path)
                    print(f"[FileUpload] Uploaded {filename or url} to {public_url}")
                    return public_url
                else:
                    print(f"[FileUpload] Upload failed for {filename or url}")
                    return None
            except Exception as upload_error:
                # Handle 409 Duplicate error - file already exists
                error_str = str(upload_error)
                if "409" in error_str or "Duplicate" in error_str or "already exists" in error_str.lower():
                    # File already exists, return existing public URL
                    public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(upload_path)
                    print(f"[FileUpload] File already exists, reusing: {public_url}")
                    return public_url
                else:
                    # Re-raise other errors
                    raise upload_error
                
        except Exception as e:
            print(f"[FileUpload] Error uploading from URL {url}: {e}")
            import traceback
            traceback.print_exc()
            return None


# Global service instance
file_upload_service = FileUploadService()

