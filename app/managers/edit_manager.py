from fastapi import HTTPException
from typing import Any, Callable

from app.services.image.image_editor import ImageEditService
from app.core.logging_config import get_logger

logger = get_logger("edit_manager")


class EditManager:
    
    def __init__(self, edit_service: ImageEditService):
        self.edit_service = edit_service

    def apply_resize(self, image_name: str, width: int, height: int) -> str:
        logger.info(f"Resizing image '{image_name}' to {width}x{height}")
        return self.edit_service.resize_image(image_name, width, height)

    def apply_grayscale(self, image_name: str) -> str:
        logger.info(f"Converting image '{image_name}' to grayscale")
        return self.edit_service.convert_to_grayscale(image_name)

    def apply_rotation(self, image_name: str, degrees: int, expand: bool = False) -> str:
        logger.info(f"Rotating image '{image_name}' by {degrees} degrees, expand={expand}")
        return self.edit_service.rotate_image(image_name, degrees, expand)

    def apply_blur(self, image_name: str, radius: float = 2.0) -> str:
        logger.info(f"Applying blur to image '{image_name}' with radius={radius}")
        return self.edit_service.blur_image(image_name, radius)

    def apply_sharpen(self, image_name: str, factor: float = 2.0, radius: float = 2.0, threshold: int = 3) -> str:
        logger.info(f"Sharpening image '{image_name}' with factor={factor}, radius={radius}, threshold={threshold}")
        return self.edit_service.sharpen_image(image_name, factor, radius, threshold)

    def apply_brightness(self, image_name: str, factor: float) -> str:
        logger.info(f"Adjusting brightness of image '{image_name}' by factor={factor}")
        return self.edit_service.adjust_brightness(image_name, factor)

    def apply_contrast(self, image_name: str, factor: float) -> str:
        logger.info(f"Adjusting contrast of image '{image_name}' by factor={factor}")
        return self.edit_service.adjust_contrast(image_name, factor)

    def apply_bulk_edits(self, image_name: str, edits: dict[str, Any]) -> dict[str, str]:
        logger.info(f"Applying bulk edits to '{image_name}': {edits}")
        results = {}

        if "resize" in edits:
            resize_params = edits["resize"]
            if isinstance(resize_params, dict):
                width = resize_params.get("width")
                height = resize_params.get("height")
            else:
                width, height = resize_params
            if width is None or height is None:
                logger.error(f"Width and height are required for resizing. Received: width={width}, height={height}")
                raise HTTPException(status_code=422, detail="Width and height are required for resizing")
            if not isinstance(width, int) or not isinstance(height, int):
                logger.error(
                    f"Width and height must be integers. Received: width={width} (type: {type(width).__name__}), "
                    f"height={height} (type: {type(height).__name__})"
                )
                raise HTTPException(status_code=422, detail="Width and height must be integers")
            results["resized"] = self.apply_resize(image_name, width, height)

        if "grayscale" in edits:
            results["grayscale"] = self.apply_grayscale(image_name)

        if "rotate" in edits:
            degrees = edits["rotate"].get("degrees", 0)
            expand = edits["rotate"].get("expand", False)
            results["rotated"] = self.apply_rotation(image_name, degrees, expand)

        if "blur" in edits:
            results["blurred"] = self.apply_blur(image_name, edits["blur"])

        if "sharpen" in edits:
            results["sharpened"] = self.apply_sharpen(image_name, **edits["sharpen"])

        if "brightness" in edits:
            results["brightness_adjusted"] = self.apply_brightness(image_name, edits["brightness"])

        if "contrast" in edits:
            results["contrast_adjusted"] = self.apply_contrast(image_name, edits["contrast"])

        logger.info(f"Completed bulk edits for '{image_name}'")
        return results

    def process_image_edit(
        self,
        image_name: str,
        edit_method: Callable[..., str],
        *args: Any,
        **kwargs: Any,
    ) -> str:
        method_name = getattr(edit_method, "__name__", "unknown")
        logger.info(f"Processing '{image_name}' using method '{method_name}'")
        try:
            result = edit_method(*args, **kwargs)
            logger.info(f"Successfully processed '{image_name}'. Result path: {result}")
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing '{image_name}' with '{method_name}': {e}")
            raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")
