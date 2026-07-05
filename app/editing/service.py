from collections.abc import Callable
from io import BytesIO
from typing import Any

from PIL import Image

from app.core.logging_config import get_logger
from app.editing import operations
from app.editing.domain.dtos import EditResultDTO
from app.editing.domain.errors import ImageEditError
from app.editing.filename import build_display_filename
from app.media.domain.enums import ImageFolder
from app.media.domain.errors import ImageNotFoundError
from app.media.repository import ImageRepository
from app.media.service import ImageService
from app.storage.base_storage import BaseImageStorage

logger = get_logger("image_edit_service")


class ImageEditService:
    def __init__(
        self,
        image_service: ImageService,
        image_repository: ImageRepository,
        storage: BaseImageStorage,
    ) -> None:
        self.image_service = image_service
        self.image_repository = image_repository
        self.storage = storage

    def _apply_edit(
        self,
        image_name: str,
        operation: Callable[..., Image.Image],
        suffix: str | None = None,
        save_format: str = "JPEG",
        **kwargs: Any,
    ) -> EditResultDTO:
        image_path = self.image_service.get_image_path(image_name, ImageFolder.UPLOADED)
        display_filename = build_display_filename(image_name, suffix)
        storage_id = self.image_repository.get_or_create_image_id(
            display_filename,
            ImageFolder.EDITED,
        )

        try:
            with Image.open(image_path) as img:
                processed_img = operation(img, **kwargs)
                img_byte_arr = BytesIO()
                processed_img.save(img_byte_arr, format=save_format.upper())
                img_byte_arr.seek(0)
                output_path = self.storage.save(
                    file=img_byte_arr,
                    folder=ImageFolder.EDITED,
                    storage_id=storage_id,
                    format=save_format,
                )
                image = self.image_repository.upsert(
                    path=output_path,
                    folder=ImageFolder.EDITED,
                    display_filename=display_filename,
                    image_id=storage_id,
                )
                return EditResultDTO(path=output_path, image=image)
        except (ImageNotFoundError, ImageEditError):
            raise
        except Exception as exc:
            logger.error("Error processing image %s: %s", image_name, exc)
            raise ImageEditError(f"Failed to process image: {exc}") from exc

    def resize_image(self, image_name: str, width: int, height: int) -> EditResultDTO:
        return self._apply_edit(
            image_name,
            operations.resize,
            suffix="resized",
            width=width,
            height=height,
        )

    def convert_to_grayscale(self, image_name: str) -> EditResultDTO:
        return self._apply_edit(image_name, operations.grayscale, suffix="gray")

    def rotate_image(self, image_name: str, degrees: int, expand: bool = False) -> EditResultDTO:
        return self._apply_edit(
            image_name,
            operations.rotate,
            suffix=f"rotated_{degrees}",
            degrees=degrees,
            expand=expand,
        )

    def blur_image(self, image_name: str, radius: float = 2.0) -> EditResultDTO:
        return self._apply_edit(
            image_name,
            operations.blur,
            suffix=f"blurred_{radius}",
            radius=radius,
        )

    def sharpen_image(
        self,
        image_name: str,
        factor: float = 2.0,
        radius: float = 2.0,
        threshold: int = 3,
    ) -> EditResultDTO:
        return self._apply_edit(
            image_name,
            operations.sharpen,
            suffix="sharpened",
            factor=factor,
            radius=radius,
            threshold=threshold,
        )

    def adjust_brightness(self, image_name: str, factor: float) -> EditResultDTO:
        return self._apply_edit(
            image_name,
            operations.adjust_brightness,
            suffix=f"brightness_{factor}",
            factor=factor,
        )

    def adjust_contrast(self, image_name: str, factor: float) -> EditResultDTO:
        return self._apply_edit(
            image_name,
            operations.adjust_contrast,
            suffix=f"contrast_{factor}",
            factor=factor,
        )
