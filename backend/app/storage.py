"""Local Storage utilities for managing file uploads"""

import os
import shutil
import base64
import binascii
import re
import hashlib
from typing import Optional, List
from fastapi import HTTPException
from app.core.config import settings

# Define storage directory
STORAGE_DIR = "static/comics"
os.makedirs(STORAGE_DIR, exist_ok=True)

class LocalStorage:
    """Handle file uploads to Local Storage"""

    def __init__(self):
        # Ensure base directory exists
        if not os.path.exists(STORAGE_DIR):
            os.makedirs(STORAGE_DIR, exist_ok=True)
    
    def _get_file_url(self, file_path: str) -> str:
        """Construct a URL for a locally stored file."""
        # Assuming static files are mounted at /static
        # file_path is relative to STORAGE_DIR (static/comics)
        # So we want /static/comics/path/to/file
        relative_path = os.path.relpath(file_path, "static")
        return f"/static/{relative_path}"

    def upload_pdf(self, file_content: bytes, comic_name: str, filename: Optional[str] = None, comic_id: Optional[int] = None) -> str:
        if not filename:
            filename = "comic.pdf"
        elif not filename.endswith('.pdf'):
            filename = f"{filename}.pdf"
        
        folder_path = self._get_comic_folder_path(comic_id)
        os.makedirs(folder_path, exist_ok=True)
        
        file_path = os.path.join(folder_path, filename)
        
        try:
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            return self._get_file_url(file_path)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save PDF locally: {str(e)}")
    
    def upload_image(self, image_data: bytes, comic_name: str, extension: str = ".png", comic_id: Optional[int] = None) -> str:
        folder_path = self._get_comic_folder_path(comic_id)
        os.makedirs(folder_path, exist_ok=True)
        
        filename = f"cover{extension}"
        file_path = os.path.join(folder_path, filename)
        
        try:
            with open(file_path, "wb") as f:
                f.write(image_data)
            
            return self._get_file_url(file_path)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save image locally: {str(e)}")
    
    def upload_base64_image(self, base64_str: str, comic_name: str, comic_id: Optional[int] = None) -> str:
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
        
        if len(data) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image too large (max 5MB)")
        
        extension = ".png"
        if "image/jpeg" in header or "image/jpg" in header:
            extension = ".jpg"
        elif "image/gif" in header:
            extension = ".gif"
        elif "image/webp" in header:
            extension = ".webp"
        
        return self.upload_image(data, comic_name, extension, comic_id=comic_id)
    
    def upload_chapter_image(self, image_data: bytes, comic_id: int, chapter_id: int, image_index: int, extension: str = ".png") -> str:
        """Upload a single chapter image."""
        folder_path = self._get_chapter_folder_path(comic_id, chapter_id)
        os.makedirs(folder_path, exist_ok=True)
        
        # Use zero-padded index for proper sorting (e.g., page_001.png, page_002.png)
        filename = f"page_{str(image_index).zfill(3)}{extension}"
        file_path = os.path.join(folder_path, filename)
        
        try:
            with open(file_path, "wb") as f:
                f.write(image_data)
            
            return self._get_file_url(file_path)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save chapter image locally: {str(e)}")
    
    def upload_chapter_images(self, images_data: List[bytes], comic_id: int, chapter_id: int, extensions: List[str] = None) -> List[str]:
        """Upload multiple chapter images and return their URLs."""
        if extensions is None:
            extensions = [".png"] * len(images_data)
        
        if len(images_data) != len(extensions):
            raise HTTPException(status_code=400, detail="Mismatch between number of images and extensions")
        
        urls = []
        for idx, (image_data, extension) in enumerate(zip(images_data, extensions), start=1):
            url = self.upload_chapter_image(image_data, comic_id, chapter_id, idx, extension)
            urls.append(url)
        
        return urls
    
    def _get_chapter_folder_path(self, comic_id: int, chapter_id: int) -> str:
        """Get the folder path for a specific chapter."""
        return os.path.join(STORAGE_DIR, str(comic_id), f"chapter_{chapter_id}")

    
    def _get_comic_folder_path(self, comic_id: Optional[int] = None) -> str:
        if comic_id is not None:
            return os.path.join(STORAGE_DIR, str(comic_id))
        # Fallback or temp handling if needed, but we prefer ID
        return os.path.join(STORAGE_DIR, "temp")

    def delete_comic_folder(self, comic_id: int) -> bool:
        folder_path = os.path.join(STORAGE_DIR, str(comic_id))
        try:
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)
            return True
        except Exception as e:
            print(f"Failed to delete comic folder locally: {str(e)}")
            return False

    def delete_file(self, file_url: str) -> bool:
        try:
            if not file_url:
                return False
            
            # URL is like /static/comics/1/cover.png
            # We need to map it back to filesystem path: static/comics/1/cover.png
            
            if file_url.startswith("/static/"):
                relative_path = file_url[len("/static/"):]
                # Prevent directory traversal
                if ".." in relative_path:
                    return False
                file_path = os.path.join("static", relative_path)
                
                if os.path.exists(file_path):
                    os.remove(file_path)
                    return True
            return False
            
        except Exception as e:
            print(f"Failed to delete file locally: {str(e)}")
            return False

# Create a singleton instance
storage_client = LocalStorage()
