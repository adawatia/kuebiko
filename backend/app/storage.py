"""Supabase Storage utilities for managing file uploads"""

import uuid
import base64
import binascii
import re
import hashlib
from typing import Optional
from supabase import create_client, Client
from fastapi import HTTPException
from app.core.config import settings


class SupabaseStorage:
    """Handle file uploads to Supabase Storage"""
    
    def __init__(self):
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise ValueError("Supabase credentials not configured. Please set SUPABASE_URL and SUPABASE_KEY environment variables.")
        
        self.client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        self.bucket_name = settings.SUPABASE_BUCKET_NAME
    
    def upload_pdf(self, file_content: bytes, comic_name: str, filename: Optional[str] = None, comic_id: Optional[int] = None) -> str:
        """
        Upload a PDF file to Supabase Storage organized by comic name.
        
        Args:
            file_content: PDF file bytes
            comic_name: Name of the comic (used for folder organization)
            filename: Optional custom filename (defaults to 'comic.pdf')
            
        Returns:
            Public URL of the uploaded file
        """
        if not filename:
            filename = "comic.pdf"
        elif not filename.endswith('.pdf'):
            filename = f"{filename}.pdf"
        
        folder_prefix = self._get_comic_folder_prefix(comic_name=comic_name, comic_id=comic_id)
        file_path = f"{folder_prefix}/{filename}"
        
        try:
            # Use upsert to replace existing file if it exists
            self.client.storage.from_(self.bucket_name).upload(
                file_path,
                file_content,
                {"content-type": "application/pdf", "upsert": "true", "cacheControl": "3600"}
            )
            
            # Get public URL
            public_url = self.client.storage.from_(self.bucket_name).get_public_url(file_path)
            return public_url
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload PDF to Supabase: {str(e)}")
    
    def upload_image(self, image_data: bytes, comic_name: str, extension: str = ".png", comic_id: Optional[int] = None) -> str:
        """
        Upload an image to Supabase Storage organized by comic name.
        
        Args:
            image_data: Image bytes
            comic_name: Name of the comic (used for folder organization)
            extension: File extension (e.g., '.png', '.jpg')
            
        Returns:
            Public URL of the uploaded image
        """
        folder_prefix = self._get_comic_folder_prefix(comic_name=comic_name, comic_id=comic_id)
        filename = f"cover{extension}"
        file_path = f"{folder_prefix}/{filename}"
        
        # Determine content type
        content_type = "image/png"
        if extension in [".jpg", ".jpeg"]:
            content_type = "image/jpeg"
        elif extension == ".gif":
            content_type = "image/gif"
        elif extension == ".webp":
            content_type = "image/webp"
        
        try:
            # Use upsert to replace existing file if it exists
            self.client.storage.from_(self.bucket_name).upload(
                file_path,
                image_data,
                {"content-type": content_type, "upsert": "true", "cacheControl": "3600"}
            )
            
            # Get public URL
            public_url = self.client.storage.from_(self.bucket_name).get_public_url(file_path)
            return public_url
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload image to Supabase: {str(e)}")
    
    def upload_base64_image(self, base64_str: str, comic_name: str, comic_id: Optional[int] = None) -> str:
        """
        Decode base64 string and upload image to Supabase organized by comic name.
        
        Args:
            base64_str: Base64 encoded image string
            comic_name: Name of the comic (used for folder organization)
            
        Returns:
            Public URL of the uploaded image
        """
        # Parse base64 string
        if "," in base64_str:
            header, encoded = base64_str.split(",", 1)
        else:
            encoded = base64_str
            header = ""
        
        try:
            data = base64.b64decode(encoded)
        except (binascii.Error, ValueError):
            raise HTTPException(status_code=400, detail="Invalid base64 image data")
        
        if not data:
            raise HTTPException(status_code=400, detail="Empty image data")
        
        # Check size (max 5MB)
        if len(data) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image too large (max 5MB)")
        
        # Determine extension
        extension = ".png"  # Default
        if "image/jpeg" in header or "image/jpg" in header:
            extension = ".jpg"
        elif "image/gif" in header:
            extension = ".gif"
        elif "image/webp" in header:
            extension = ".webp"
        
        return self.upload_image(data, comic_name, extension, comic_id=comic_id)
    
    def _sanitize_folder_name(self, name: str) -> str:
        """
        Sanitize a comic name to be used as a folder name.
        Removes special characters and spaces.
        
        Args:
            name: Original comic name
            
        Returns:
            Sanitized folder name
        """
        if not name or not name.strip():
            raise HTTPException(status_code=400, detail="Comic name cannot be empty")
        
        # Replace spaces with hyphens, remove special characters
        sanitized = re.sub(r'[^\w\s-]', '', name)
        sanitized = re.sub(r'[-\s]+', '-', sanitized)
        sanitized = sanitized.strip('-').lower()
        
        # Handle edge case where sanitization results in empty string
        if not sanitized:
            # Use a hash of the original name as fallback
            sanitized = hashlib.md5(name.encode()).hexdigest()[:8]
        
        return sanitized

    def _get_comic_folder_prefix(self, comic_name: str, comic_id: Optional[int] = None) -> str:
        """Return a stable folder prefix for a comic.

        Prefer numeric ID (stable even if title changes), fallback to sanitized name.
        """
        if comic_id is not None:
            return f"comics/{comic_id}"

        safe_comic_name = self._sanitize_folder_name(comic_name)
        return f"comics/{safe_comic_name}"

    def delete_comic_folder(self, comic_id: int) -> bool:
        """Delete all objects within a comic folder."""
        prefix = f"comics/{comic_id}"
        try:
            objects = self._list_objects(prefix)
            if not objects:
                return True

            paths = []
            for obj in objects:
                name = obj.get("name") if isinstance(obj, dict) else None
                if name:
                    paths.append(f"{prefix}/{name}")

            if paths:
                self.client.storage.from_(self.bucket_name).remove(paths)
            return True
        except Exception as e:
            print(f"Failed to delete comic folder from Supabase: {str(e)}")
            return False

    def _list_objects(self, prefix: str):
        """List objects in a prefix, compatible with multiple supabase-py versions."""
        storage = self.client.storage.from_(self.bucket_name)
        try:
            return storage.list(prefix, {"limit": 1000, "offset": 0})
        except TypeError:
            return storage.list(prefix)
    
    def delete_file(self, file_url: str) -> bool:
        """
        Delete a file from Supabase Storage.
        
        Args:
            file_url: Public URL of the file
            
        Returns:
            True if successful
        """
        try:
            # Extract file path from URL
            # URL format: https://{project}.supabase.co/storage/v1/object/public/{bucket}/{path}
            if not file_url:
                return False
            
            # Parse the path from URL
            parts = file_url.split(f"{self.bucket_name}/")
            if len(parts) < 2:
                return False
            
            file_path = parts[1]
            
            self.client.storage.from_(self.bucket_name).remove([file_path])
            return True
            
        except Exception as e:
            # Log error but don't raise exception for deletion failures
            print(f"Failed to delete file from Supabase: {str(e)}")
            return False


# Create a singleton instance
supabase_storage = SupabaseStorage()
