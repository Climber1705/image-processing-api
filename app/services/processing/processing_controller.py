from PIL import Image, ImageOps, ImageFilter, ImageEnhance
import os
from pathlib import Path
from typing import Union, Tuple

from app.core.settings import settings
from app.services.file_io.file_query import ImageQuery


class ImageProcessing:
    """Service for processing and manipulating images using Pillow."""

    def __init__(self, image_query: ImageQuery):
        """
        Initialize the ImageProcessing.
        
        Args:
            directory_manager: Manager for handling directories
        """
        self.image_query = image_query
        self.upload_folder = settings.UPLOAD_FOLDER
        self.processed_folder = settings.PROCESSED_FOLDER
        
        # Ensure processed directory exists
        os.makedirs(self.processed_folder, exist_ok=True)

    def _get_output_path(self, image_path: str, suffix: str = None) -> str:
        """
        Generate the output path for processed images.
        
        Args:
            image_path: Path to the original image
            suffix: Optional suffix to add to the filename
            
        Returns:
            Path to save the processed image
        """
        # Get base filename and extension
        basename = os.path.basename(image_path)
        filename, ext = os.path.splitext(basename)
        
        # Create output filename with optional suffix
        if suffix:
            output_filename = f"{filename}_{suffix}{ext}"
        else:
            output_filename = basename
            
        # Create output directory if it doesn't exist
        rel_path = os.path.relpath(os.path.dirname(image_path), self.upload_folder)
        output_dir = os.path.join(self.processed_folder, rel_path)
        os.makedirs(output_dir, exist_ok=True)
        
        return os.path.join(output_dir, output_filename)

    def _process_image(self, image_name: str, operation, suffix: str = None, **kwargs) -> str:
        """
        Generic method to process an image and save the result.
        
        Args:
            image_path: Path to the input image
            operation: Function to apply to the image
            suffix: Suffix to add to the output filename
            **kwargs: Additional arguments for the operation
            
        Returns:
            Path to the processed image
        """
        image_path = self.image_query.get_image_path(image_name, "uploads")
        try:
            with Image.open(image_path) as img:
                processed_img = operation(img, **kwargs)
                output_path = self._get_output_path(image_path, suffix)
                processed_img.save(output_path, quality=95)
                return output_path
        except Exception as e:
            raise ValueError(f"Error processing image {image_path}: {str(e)}")

    def resize_image(self, image_name: str, width: int, height: int) -> str:
        """
        Resize an image to the specified dimensions.
        
        Args:
            image_name: Name of the image e.g test1.png
            width: Target width in pixels
            height: Target height in pixels
            
        Returns:
            Path to the resized image
        """
        return self._process_image(
            image_name, 
            lambda img, **kwargs: img.resize((kwargs['width'], kwargs['height']), Image.LANCZOS),
            suffix="resized",
            width=width,
            height=height
        )

    def convert_to_grayscale(self, image_name: str) -> str:
        """
        Convert an image to grayscale.
        
        Args:
            image_name: Name of the input image
            
        Returns:
            Path to the grayscale image
        """

        return self._process_image(
            image_name,
            lambda img, **kwargs: ImageOps.grayscale(img),
            suffix="gray"
        )

    def rotate_image(self, image_name: str, degrees: int, expand: bool = False) -> str:
        """
        Rotate an image by the specified degrees.
        
        Args:
            image_name: Name of teh 
            degrees: Rotation angle in degrees (counter-clockwise)
            expand: Whether to expand the output image to fit rotated content
            
        Returns:
            Path to the rotated image
        """
        return self._process_image(
            image_name,
            lambda img, **kwargs: img.rotate(
                kwargs['degrees'], 
                expand=kwargs['expand'], 
                resample=Image.BICUBIC
            ),
            suffix=f"rotated_{degrees}",
            degrees=degrees,
            expand=expand
        )

    def crop_image(self, image_name: str, left: int, upper: int, right: int, lower: int) -> str:
        """
        Crop an image to the specified coordinates.
        
        Args:
            image_path: Path to the input image
            left: Left coordinate
            upper: Upper coordinate
            right: Right coordinate
            lower: Lower coordinate
            
        Returns:
            Path to the cropped image
        """
        return self._process_image(
            image_name,
            lambda img, **kwargs: img.crop((
                kwargs['left'], 
                kwargs['upper'], 
                kwargs['right'], 
                kwargs['lower']
            )),
            suffix="cropped",
            left=left,
            upper=upper,
            right=right,
            lower=lower
        )

    def blur_image(self, image_name: str, radius: float = 2.0) -> str:
        """
        Apply Gaussian blur to an image.
        
        Args:
            image_path: Path to the input image
            radius: Blur radius
            
        Returns:
            Path to the blurred image
        """
        return self._process_image(
            image_name,
            lambda img, **kwargs: img.filter(ImageFilter.GaussianBlur(kwargs['radius'])),
            suffix=f"blurred_{radius}",
            radius=radius
        )

    def sharpen_image(self, image_name: str, factor: float = 2.0, radius: float = 2.0, threshold: int = 3) -> str:
        """
        Sharpen an image using the UnsharpMask filter.
        
        Args:
            image_path: Path to the input image
            factor: Sharpening factor
            radius: Filter radius
            threshold: Threshold controlling the minimum brightness change
            
        Returns:
            Path to the sharpened image
        """
        return self._process_image(
            image_name,
            lambda img, **kwargs: img.filter(ImageFilter.UnsharpMask(
                radius=kwargs['radius'],
                percent=int(kwargs['factor'] * 100),
                threshold=kwargs['threshold']
            )),
            suffix="sharpened",
            factor=factor,
            radius=radius,
            threshold=threshold
        )
        
    def adjust_brightness(self, image_name: str, factor: float) -> str:
        """
        Adjust the brightness of an image.
        
        Args:
            image_path: Path to the input image
            factor: Brightness factor (1.0 is unchanged, <1.0 darkens, >1.0 brightens)
            
        Returns:
            Path to the brightness-adjusted image
        """
        return self._process_image(
            image_name,
            lambda img, **kwargs: ImageOps.autocontrast(
                img.point(lambda p: p * kwargs['factor'])
            ),
            suffix=f"brightness_{factor}",
            factor=factor
        )
    
    def adjust_contrast(self, image_name: str, factor: float) -> str:
        """
        Adjust the contrast of an image.
        
        Args:
            image_path: Path to the input image
            factor: Contrast factor (1.0 is unchanged, <1.0 decreases, >1.0 increases)
            
        Returns:
            Path to the contrast-adjusted image
        """
        return self._process_image(
            image_name,
            lambda img, **kwargs: ImageEnhance.Contrast(img).enhance(kwargs['factor']),
            suffix=f"contrast_{factor}",
            factor=factor
        )
        
    def apply_watermark(self, image_name: str, watermark_path: str, position: Tuple[int, int] = None, opacity: float = 0.3) -> str:
        """
        Apply a watermark to an image.
        
        Args:
            image_path: Path to the input image
            watermark_path: Path to the watermark image
            position: (x, y) position for the watermark, defaults to center if None
            opacity: Opacity of the watermark (0.0 to 1.0)
            
        Returns:
            Path to the watermarked image
        """
        def apply_watermark_op(img, **kwargs):
            with Image.open(kwargs['watermark_path']).convert('RGBA') as watermark:
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Create a transparent layer for the watermark
                layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
                
                # Calculate position if not specified
                if kwargs['position'] is None:
                    position = (
                        (img.width - watermark.width) // 2,
                        (img.height - watermark.height) // 2
                    )
                else:
                    position = kwargs['position']
                
                # Apply opacity to watermark
                watermark_with_opacity = Image.new('RGBA', watermark.size, (0, 0, 0, 0))
                for x in range(watermark.width):
                    for y in range(watermark.height):
                        r, g, b, a = watermark.getpixel((x, y))
                        watermark_with_opacity.putpixel((x, y), (r, g, b, int(a * kwargs['opacity'])))
                
                # Paste the watermark onto the layer
                layer.paste(watermark_with_opacity, position)
                
                # Composite the layer with the image
                return Image.alpha_composite(img, layer).convert('RGB')
        
        return self._process_image(
            image_name,
            apply_watermark_op,
            suffix="watermarked",
            watermark_path=watermark_path,
            position=position,
            opacity=opacity
        )