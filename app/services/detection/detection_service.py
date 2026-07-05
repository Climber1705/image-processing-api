import os
import torch
from io import BytesIO
from random import randint
from tempfile import SpooledTemporaryFile
from fastapi import Depends, Request, UploadFile
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Tuple, Annotated, Union



from app.core.config import settings
from app.services.image.storage.local_storage import LocalImageStorage, get_local_image_storage
from app.services.inference.engine import InferenceEngine
from app.core.logging_config import get_logger

LocalImageStorageDep = Annotated[LocalImageStorage, Depends(get_local_image_storage)]

logger = get_logger("detection_service")


class ObjectDetectionService:
    def __init__(
        self,
        inference_engine: InferenceEngine,
        local_storage: LocalImageStorage,
        confidence_threshold: float | None = None,
    ) -> None:
        self.engine = inference_engine
        self.processor = inference_engine.processor
        self.model = inference_engine.model
        self.confidence_threshold = (
            confidence_threshold
            if confidence_threshold is not None
            else settings.CONFIDENCE_THRESHOLD
        )
        self.local_storage = local_storage

    def _get_font(self, size: int):
        try:
            return ImageFont.truetype("arial.ttf", size)
        except IOError:
            logger.warning("Arial font not found, using default font.")
            return ImageFont.load_default()

    def _get_random_colour(self) -> Tuple[str, Tuple[int, int, int]]:
        r, g, b = randint(0, 255), randint(0, 255), randint(0, 255)
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        return hex_color, (r, g, b)

    def _get_text_colour(self, rgb: Tuple[int, int, int]) -> str:
        r, g, b = rgb
        brightness = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return "#ffffff" if brightness < 0.5 else "#000000"

    def _pillow_to_uploadfile(self, image: Image.Image, filename: str = "image.png") -> UploadFile:
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format=image.format or "PNG")
        img_byte_arr.seek(0)

        temp_file = SpooledTemporaryFile()
        temp_file.write(img_byte_arr.read())
        temp_file.seek(0)

        return UploadFile(filename=filename, file=temp_file)

    def get_bounding_boxes(self, image_path: str) -> str:
        image = Image.open(image_path)
        image_copy = image.copy()
        draw = ImageDraw.Draw(image_copy)
        font = self._get_font(16)

        inputs = self.processor(images=image, return_tensors="pt")
        outputs = self.model(**inputs)

        target_sizes = torch.tensor([image.size[::-1]])
        results = self.processor.post_process_object_detection(
            outputs, target_sizes=target_sizes, threshold=self.confidence_threshold
        )[0]

        for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
            box = [round(coord) for coord in box.tolist()]
            x, y, x2, y2 = box

            class_name = self.model.config.id2label[label.item()]
            confidence = score.item()

            colour, rgb = self._get_random_colour()
            draw.rectangle([x, y, x2, y2], outline=colour, width=3)

            text = f"{class_name}: {confidence:.2f}"
            text_bbox = draw.textbbox((x, y - 20), text, font=font)
            draw.rectangle(text_bbox, fill=colour)
            draw.text((x, y - 20), text, fill=self._get_text_colour(rgb), font=font)

        original_filename = os.path.basename(image_path)
        name, ext = os.path.splitext(original_filename)
        new_filename = f"{name}_bounding_boxes{ext}"

        output_path = self.local_storage.save(
            file=self._pillow_to_uploadfile(image_copy, filename=new_filename),
            folder="detected",
            filename=new_filename,
            format=image.format,
        )

        logger.info(f"Bounding boxes saved to: {output_path}")
        return output_path

    def get_detected_objects(self, image_path: str) -> List[Dict[str, Union[str, float, List[float]]]]:
        image = Image.open(image_path)

        inputs = self.processor(images=image, return_tensors="pt")
        outputs = self.model(**inputs)

        target_sizes = torch.tensor([image.size[::-1]])
        results = self.processor.post_process_object_detection(
            outputs, target_sizes=target_sizes, threshold=self.confidence_threshold
        )[0]

        detections = []
        for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
            detections.append({
                "label": self.model.config.id2label[label.item()],
                "confidence": score.item(),
                "box": box.tolist(),
            })

        logger.info(f"Detected {len(detections)} objects.")
        return detections


def get_object_detection_service(
    request: Request,
    local_storage: LocalImageStorageDep,
) -> ObjectDetectionService:
    inference_engine: InferenceEngine | None = getattr(request.app.state, "inference_engine", None)
    if inference_engine is None:
        raise RuntimeError("Inference engine is not initialized")

    return ObjectDetectionService(
        inference_engine=inference_engine,
        local_storage=local_storage,
    )
