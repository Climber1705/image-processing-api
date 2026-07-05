from io import BytesIO
from pathlib import Path
from fastapi import HTTPException
from PIL import Image
from typing import Any, Callable, Optional

from app.core.logging_config import get_logger
from app.media.repository import ImageRepository
from app.media.service import ImageService
from app.storage.base_storage import BaseImageStorage

logger = get_logger("image_editor")


class ImageEditService:
    def __init__(
        self,
        image_service: ImageService,
        image_repository: ImageRepository,
        storage: BaseImageStorage,
    ):
        self.image_service = image_service
        self.image_repository = image_repository
        self.storage = storage

    def _build_display_filename(self, image_name: str, suffix: Optional[str] = None) -> str:
        path = Path(image_name)
        stem = path.stem
        ext = path.suffix or ".jpg"
        if suffix:
            return f"{stem}_{suffix}{ext}"
        return f"{stem}{ext}"

    def _process_image(
        self,
        image_name: str,
        operation: Callable[..., Image.Image],
        suffix: Optional[str] = None,
        save_format: str = "JPEG",
        **kwargs: Any,
    ) -> str:
        image_path = self.image_service.get_image_path(image_name, "uploaded")
        display_filename = self._build_display_filename(image_name, suffix)
        storage_id = self.image_repository.resolve_image_id(display_filename, "edited")

        try:
            with Image.open(image_path) as img:
                processed_img = operation(img, **kwargs)
                img_byte_arr = BytesIO()
                processed_img.save(img_byte_arr, format=save_format.upper())
                img_byte_arr.seek(0)
                output_path = self.storage.save(
                    file=img_byte_arr,
                    folder="edited",
                    storage_id=storage_id,
                    format=save_format,
                )
                self.image_repository.create_record(
                    path=output_path,
                    folder="edited",
                    display_filename=display_filename,
                    image_id=storage_id,
                )
                logger.info(f"Successfully processed image {image_name} with {suffix} operation.")
                return output_path
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing image {image_name}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to process image: {e}")

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
        from PIL import ImageOps

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
        from PIL import ImageFilter

        return self._process_image(
            image_name,
            lambda img, **kwargs: img.filter(ImageFilter.GaussianBlur(kwargs["radius"])),
            suffix=f"blurred_{radius}",
            radius=radius,
        )

    def sharpen_image(self, image_name: str, factor: float = 2.0, radius: float = 2.0, threshold: int = 3) -> str:
        logger.info(f"Sharpening image {image_name} with factor {factor}, radius {radius}, threshold {threshold}.")
        from PIL import ImageFilter

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
        from PIL import ImageOps

        return self._process_image(
            image_name,
            lambda img, **kwargs: ImageOps.autocontrast(img.point(lambda p: p * kwargs["factor"])),
            suffix=f"brightness_{factor}",
            factor=factor,
        )

    def adjust_contrast(self, image_name: str, factor: float) -> str:
        logger.info(f"Adjusting contrast of image {image_name} by factor {factor}.")
        from PIL import ImageEnhance

        return self._process_image(
            image_name,
            lambda img, **kwargs: ImageEnhance.Contrast(img).enhance(kwargs["factor"]),
            suffix=f"contrast_{factor}",
            factor=factor,
        )
