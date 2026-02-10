"""ImageKit Storage utilities for managing file uploads"""

import os
import base64
import binascii
from typing import Optional, List
from fastapi import HTTPException
from imagekitio import ImageKit
from app.core.config import settings

class ImageKitStorage:
    """Handle file uploads to ImageKit"""

    def __init__(self):
        if not settings.IMAGEKIT_PRIVATE_KEY or not settings.IMAGEKIT_URL_ENDPOINT:
            raise ValueError("ImageKit credentials not configured. Please set IMAGEKIT_PRIVATE_KEY and IMAGEKIT_URL_ENDPOINT in environment variables.")
        
        # ImageKit SDK v5+ only accepts private_key in constructor
        # url_endpoint is used when generating URLs via helper methods
        self.imagekit = ImageKit(
            private_key=settings.IMAGEKIT_PRIVATE_KEY
        )
        self.public_key = settings.IMAGEKIT_PUBLIC_KEY  # Store for client-side use if needed
        self.url_endpoint = settings.IMAGEKIT_URL_ENDPOINT  # Store for URL generation
    
    def upload_pdf(self, file_content: bytes, comic_name: str, filename: Optional[str] = None, comic_id: Optional[int] = None) -> str:
        """Upload PDF to ImageKit (Note: ImageKit is primarily for images, but can store PDFs)"""
        if not filename:
            filename = "comic.pdf"
        elif not filename.endswith('.pdf'):
            filename = f"{filename}.pdf"
        
        folder_path = self._get_comic_folder_path(comic_id)
        
        try:
            result = self.imagekit.files.upload(
                file=file_content,
                file_name=filename,
                folder=folder_path,
                use_unique_file_name=False
            )
            
            return result.url
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload PDF to ImageKit: {str(e)}")
    
    def upload_image(self, image_data: bytes, comic_name: str, extension: str = ".png", comic_id: Optional[int] = None) -> str:
        """Upload image to ImageKit"""
        folder_path = self._get_comic_folder_path(comic_id)
        filename = f"cover{extension}"
        
        try:
            result = self.imagekit.files.upload(
                file=image_data,
                file_name=filename,
                folder=folder_path,
                use_unique_file_name=False
            )
            
            return result.url
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload image to ImageKit: {str(e)}")
    
    def upload_base64_image(self, base64_str: str, comic_name: str, comic_id: Optional[int] = None) -> str:
        """Upload base64 encoded image to ImageKit"""
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
        """Upload a single chapter image to ImageKit"""
        folder_path = self._get_chapter_folder_path(comic_id, chapter_id)
        
        # Use zero-padded index for proper sorting (e.g., page_001.png, page_002.png)
        filename = f"page_{str(image_index).zfill(3)}{extension}"
        
        try:
            result = self.imagekit.files.upload(
                file=image_data,
                file_name=filename,
                folder=folder_path,
                use_unique_file_name=False
            )
            
            return result.url
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload chapter image to ImageKit: {str(e)}")
    
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
    
    def generate_signed_url(self, image_url: str, expires_in: int = 3600) -> str:
        """
        Generate a signed URL for secure image access.
        
        Args:
            image_url: The original ImageKit URL
            expires_in: Time in seconds until URL expires (default: 1 hour)
        
        Returns:
            Signed URL that expires after the specified time
        """
        try:
            # Extract the path from the full URL
            if self.url_endpoint in image_url:
                path = image_url.replace(self.url_endpoint, "")
                if not path.startswith("/"):
                    path = "/" + path
                
                # Generate signed URL using ImageKit helper
                signed_url = self.imagekit.helper.build_url(
                    url_endpoint=self.url_endpoint,
                    src=path,
                    signed=True,
                    expire_seconds=expires_in
                )
                
                return signed_url
            
            return image_url  # Return original if not an ImageKit URL
            
        except Exception as e:
            print(f"Failed to generate signed URL: {str(e)}")
            return image_url  # Fallback to original URL
    
    def sign_urls_in_list(self, urls: List[str], expires_in: int = 3600) -> List[str]:
        """Generate signed URLs for a list of image URLs"""
        return [self.generate_signed_url(url, expires_in) for url in urls if url]
    
    def _get_chapter_folder_path(self, comic_id: int, chapter_id: int) -> str:
        """Get the folder path for a specific chapter in ImageKit"""
        return f"/comics/{comic_id}/chapter_{chapter_id}"
    
    def _get_comic_folder_path(self, comic_id: Optional[int] = None) -> str:
        """Get the folder path for a comic in ImageKit"""
        if comic_id is not None:
            return f"/comics/{comic_id}"
        return "/comics/temp"

    def delete_comic_folder(self, comic_id: int) -> bool:
        """Delete all files in a comic's folder from ImageKit"""
        folder_path = f"/comics/{comic_id}"
        
        try:
            # List all files in the folder
            list_result = self.imagekit.files.list(
                path=folder_path
            )
            
            # Delete each file
            for file in list_result.response_metadata.raw:
                try:
                    self.imagekit.files.delete(file['fileId'])
                except Exception as e:
                    print(f"Failed to delete file {file.get('fileId')}: {str(e)}")
            
            return True
        except Exception as e:
            print(f"Failed to delete comic folder from ImageKit: {str(e)}")
            return False

    def delete_file(self, file_url: str) -> bool:
        """Delete a file from ImageKit by its URL"""
        try:
            if not file_url:
                return False
            
            # Extract file_id from URL or search for the file
            # ImageKit URLs typically contain the file path
            # We need to get the file_id first by listing files with the path
            
            # Extract the path from the URL
            # URL format: https://ik.imagekit.io/your_id/path/to/file.ext
            if self.url_endpoint in file_url:
                # Remove the base URL endpoint to get the path
                path = file_url.replace(self.url_endpoint, "")
                if path.startswith("/"):
                    path = path[1:]  # Remove leading slash
                
                # List files to find the file_id
                try:
                    # Get filename from path
                    filename = path.split('/')[-1]
                    
                    # Search for the file by name
                    list_result = self.imagekit.files.list(
                        search_query=f'name="{filename}"'
                    )
                    
                    # Find matching file by full path or URL
                    for file in list_result.response_metadata.raw:
                        if file.get('url') == file_url or file.get('filePath') == f"/{path}":
                            self.imagekit.files.delete(file['fileId'])
                            return True
                except Exception as e:
                    print(f"Failed to find file for deletion: {str(e)}")
            
            return False
            
        except Exception as e:
            print(f"Failed to delete file from ImageKit: {str(e)}")
            return False

# Create a singleton instance
storage_client = ImageKitStorage()
