from PIL import Image, ImageOps, ImageFilter, ImageEnhance
from pathlib import Path
from typing import Annotated, Dict, Callable, Any, Optional
from fastapi import Depends, HTTPException

import os

from app.services.image.crud_operations import ImageCRUDService, get_image_crud_service
from app.core.dependencies import get_directories
from app.core.logging_config import get_logger

logger = get_logger("image_editor")

ImageCRUDServiceDep = Annotated[ImageCRUDService, Depends(get_image_crud_service)]
DirectoriesDep = Annotated[Dict[str, Path], Depends(get_directories)]


class ImageEditService:
    def __init__(self, image_crud: ImageCRUDServiceDep, directories: DirectoriesDep):
        self.image_crud = image_crud
        self.directories = directories

    def _get_output_path(self, image_path: str, suffix: Optional[str] = None) -> str:
        filename, ext = os.path.splitext(os.path.basename(image_path))
        output_filename = f"{filename}_{suffix}{ext}" if suffix else f"{filename}{ext}"
        return str(self.directories["edited"] / output_filename)

    def _process_image(
        self,
        image_name: str,
        operation: Callable[[Image.Image, ...], Image.Image],
        suffix: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        image_path = self.image_crud.get_image_path(image_name, "uploaded")
        try:
            with Image.open(image_path) as img:
                processed_img = operation(img, **kwargs)
                output_path = self._get_output_path(image_path, suffix)
                processed_img.save(output_path, quality=95)
                logger.info(f"Successfully processed image {image_name} with {suffix} operation.")
                return output_path
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing image {image_name}: {e}")
            raise ValueError(f"Error processing image {image_path}: {e}")

    def resize_image(self, image_name: str, width: int, height: int) -> str:
        logger.info(f"Resizing image {image_name} to {width}x{height}.")
        return self._process_image(
            image_name,
            lambda img, **kwargs: img.resize((kwargs["width"], kwargs["height"]), Image.LANCZOS),
            suffix="resized",
            width=width,
            height=height,
        )

    def convert_to_grayscale(self, image_name: str) -> str:
        logger.info(f"Converting image {image_name} to grayscale.")
        return self._process_image(
            image_name,
            lambda img, **_: ImageOps.grayscale(img),
            suffix="gray",
        )

    def rotate_image(self, image_name: str, degrees: int, expand: bool = False) -> str:
        logger.info(f"Rotating image {image_name} by {degrees} degrees. Expand: {expand}.")
        return self._process_image(
            image_name,
            lambda img, **kwargs: img.rotate(kwargs["degrees"], expand=kwargs["expand"], resample=Image.BICUBIC),
            suffix=f"rotated_{degrees}",
            degrees=degrees,
            expand=expand,
        )

    def blur_image(self, image_name: str, radius: float = 2.0) -> str:
        logger.info(f"Applying blur to image {image_name} with radius {radius}.")
        return self._process_image(
            image_name,
            lambda img, **kwargs: img.filter(ImageFilter.GaussianBlur(kwargs["radius"])),
            suffix=f"blurred_{radius}",
            radius=radius,
        )

    def sharpen_image(self, image_name: str, factor: float = 2.0, radius: float = 2.0, threshold: int = 3) -> str:
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
        logger.info(f"Adjusting brightness of image {image_name} by factor {factor}.")
        return self._process_image(
            image_name,
            lambda img, **kwargs: ImageOps.autocontrast(img.point(lambda p: p * kwargs["factor"])),
            suffix=f"brightness_{factor}",
            factor=factor,
        )

    def adjust_contrast(self, image_name: str, factor: float) -> str:
        logger.info(f"Adjusting contrast of image {image_name} by factor {factor}.")
        return self._process_image(
            image_name,
            lambda img, **kwargs: ImageEnhance.Contrast(img).enhance(kwargs["factor"]),
            suffix=f"contrast_{factor}",
            factor=factor,
        )


def get_image_edit_service(
    image_crud: ImageCRUDServiceDep,
    directories: DirectoriesDep,
) -> ImageEditService:
    return ImageEditService(image_crud=image_crud, directories=directories)
