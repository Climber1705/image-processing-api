import logging
from fastapi import HTTPException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("file_handler")


class ImageVerfication:
    """
    Validates image formats and extensions.
    """
    
    # Map of supported formats to their file extensions
    FORMAT_EXTENSIONS = {
        "JPEG": ".jpg",
        "JPG": ".jpg",
        "PNG": ".png",
        "GIF": ".gif",
        "BMP": ".bmp",
        "TIFF": ".tiff",
        "WEBP": ".webp"
    }
    
    def validate_format(self, format: str) -> str:
        """
        Validate that the specified format is supported.
        
        Args:
            format: Image format to validate
            
        Returns:
            Normalized format string
            
        Raises:
            HTTPException: If format is not supported
        """
        format = format.upper()
        if format not in self.FORMAT_EXTENSIONS:
            supported_formats = ", ".join(self.FORMAT_EXTENSIONS.keys())
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image format: {format}. Supported formats: {supported_formats}"
            )
        return format
    
    def get_extension(self, format: str) -> str:
        """
        Get the file extension for a given format.
        
        Args:
            format: Image format
            
        Returns:
            File extension including the dot (e.g., '.jpg')
            
        Raises:
            HTTPException: If format is not supported
        """
        format = self.validate_format(format)
        return self.FORMAT_EXTENSIONS[format]