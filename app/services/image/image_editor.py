from PIL import Image, ImageOps, ImageFilter, ImageEnhance
from pathlib import Path
from typing import Annotated, Dict
from fastapi import Depends, HTTPException

import os

from app.services.image.crud_operations import ImageCRUDService, get_image_crud_service
from app.core.dependencies import get_directories
from app.core.logging_config import get_logger

# Initialize the logger
logger = get_logger("image_editor")

ImageCRUDServiceDep = Annotated[ImageCRUDService, Depends(get_image_crud_service)]
DirectoriesDep = Annotated[Dict[str, Path], Depends(get_directories)]


class ImageEditService:
    """
    Service for performing image editing operations like resizing, rotating, cropping, etc.
    """
    
    def __init__(self, image_crud: ImageCRUDServiceDep, directories: DirectoriesDep):
        """
        Initialize the ImageEditService with the image CRUD operations and directories.

        @param image_crud: Dependency injection for ImageCRUDService.
        @param directories: Directories for image storage locations.
        """
        self.image_crud = image_crud
        self.directories = directories

    def _get_output_path(self, image_path: str, suffix: str | None = None) -> str:
        """
        Generate the output file path for a processed image based on the original file name and suffix.

        @param image_path: The path of the original image.
        @param suffix: A suffix to be added to the output filename (e.g., "resized").
        @returns: A string representing the output file path for the processed image.
        """
        filename, ext = os.path.splitext(os.path.basename(image_path))
        output_filename = f"{filename}_{suffix}{ext}" if suffix else f"{filename}{ext}"

        output_dir = self.directories["edited"]
        output_path = output_dir / output_filename

        return str(output_path)

    def _process_image(self, image_name: str, operation, suffix: str | None = None, **kwargs) -> str:
        """
        Apply an image processing operation and save the result.

        @param image_name: The name of the image to be processed.
        @param operation: The operation (e.g., resize, rotate) to be performed on the image.
        @param suffix: A suffix to indicate the type of operation performed (e.g., "resized").
        @param kwargs: Additional arguments required for the operation.
        @returns: The path where the processed image is saved.
        @raises ValueError: If there is an error processing the image.
        """
        image_path = self.image_crud.get_image_path(image_name, "uploaded")
        try:
            # Open the image file and apply the operation
            with Image.open(image_path) as img:
                processed_img = operation(img, **kwargs)
                output_path = self._get_output_path(image_path, suffix)
                processed_img.save(output_path, quality=95)
                
                logger.info(f"Successfully processed image {image_name} with {suffix} operation.")
                return output_path
        except Exception as e:
            logger.error(f"Error processing image {image_name}: {e}")
            raise ValueError(f"Error processing image {image_path}: {e}")

    def resize_image(self, image_name: str, width: int, height: int) -> str:
        """
        Resize an image to the specified width and height.

        @param image_name: The name of the image to resize.
        @param width: The new width for the image.
        @param height: The new height for the image.
        @returns: The path where the resized image is saved.
        """
        logger.info(f"Resizing image {image_name} to {width}x{height}.")
        return self._process_image(
            image_name,
            lambda img, **kwargs: img.resize((kwargs["width"], kwargs["height"]), Image.LANCZOS),
            suffix="resized",
            width=width,
            height=height,
        )

    def convert_to_grayscale(self, image_name: str) -> str:
        """
        Convert an image to grayscale.

        @param image_name: The name of the image to convert.
        @returns: The path where the grayscale image is saved.
        """
        logger.info(f"Converting image {image_name} to grayscale.")
        return self._process_image(
            image_name,
            lambda img, **_: ImageOps.grayscale(img),
            suffix="gray",
        )

    def rotate_image(self, image_name: str, degrees: int, expand: bool = False) -> str:
        """
        Rotate an image by a specified number of degrees.

        @param image_name: The name of the image to rotate.
        @param degrees: The number of degrees to rotate the image.
        @param expand: Whether to expand the image to fit the rotated version.
        @returns: The path where the rotated image is saved.
        """
        logger.info(f"Rotating image {image_name} by {degrees} degrees. Expand: {expand}.")
        return self._process_image(
            image_name,
            lambda img, **kwargs: img.rotate(kwargs["degrees"], expand=kwargs["expand"], resample=Image.BICUBIC),
            suffix=f"rotated_{degrees}",
            degrees=degrees,
            expand=expand,
        )

    def blur_image(self, image_name: str, radius: float = 2.0) -> str:
        """
        Apply a blur effect to an image.

        @param image_name: The name of the image to blur.
        @param radius: The radius of the blur effect.
        @returns: The path where the blurred image is saved.
        """
        logger.info(f"Applying blur to image {image_name} with radius {radius}.")
        return self._process_image(
            image_name,
            lambda img, **kwargs: img.filter(ImageFilter.GaussianBlur(kwargs["radius"])),
            suffix=f"blurred_{radius}",
            radius=radius,
        )

    def sharpen_image(self, image_name: str, factor: float = 2.0, radius: float = 2.0, threshold: int = 3) -> str:
        """
        Apply a sharpening filter to an image.

        @param image_name: The name of the image to sharpen.
        @param factor: The intensity of the sharpen effect.
        @param radius: The radius of the sharpening effect.
        @param threshold: The threshold for sharpening.
        @returns: The path where the sharpened image is saved.
        """
        logger.info(f"Sharpening image {image_name} with factor {factor}, radius {radius}, threshold {threshold}.")
        return self._process_image(
            image_name,
            lambda img, **kwargs: img.filter(
                ImageFilter.UnsharpMask(
                    radius=kwargs["radius"],
                    percent=int(kwargs["factor"] * 100),
                    threshold=kwargs["threshold"],
                )
            ),
            suffix="sharpened",
            factor=factor,
            radius=radius,
            threshold=threshold,
        )

    def adjust_brightness(self, image_name: str, factor: float) -> str:
        """
        Adjust the brightness of an image.

        @param image_name: The name of the image to adjust.
        @param factor: The factor by which to adjust brightness (1.0 means no change).
        @returns: The path where the brightness-adjusted image is saved.
        """
        logger.info(f"Adjusting brightness of image {image_name} by factor {factor}.")
        return self._process_image(
            image_name,
            lambda img, **kwargs: ImageOps.autocontrast(
                img.point(lambda p: p * kwargs["factor"])
            ),
            suffix=f"brightness_{factor}",
            factor=factor,
        )

    def adjust_contrast(self, image_name: str, factor: float) -> str:
        """
        Adjust the contrast of an image.

        @param image_name: The name of the image to adjust.
        @param factor: The factor by which to adjust contrast (1.0 means no change).
        @returns: The path where the contrast-adjusted image is saved.
        """
        logger.info(f"Adjusting contrast of image {image_name} by factor {factor}.")
        return self._process_image(
            image_name,
            lambda img, **kwargs: ImageEnhance.Contrast(img).enhance(kwargs["factor"]),
            suffix=f"contrast_{factor}",
            factor=factor,
        )


def get_image_edit_service(
    image_crud: ImageCRUDServiceDep,
    directories: DirectoriesDep
) -> ImageEditService:
    """
    Dependency injection for the ImageEditService.

    @param image_crud: Image CRUD service instance.
    @param directories: Directories configuration.
    @returns: An instance of the ImageEditService.
    """
    return ImageEditService(
        image_crud=image_crud,
        directories=directories
    )
