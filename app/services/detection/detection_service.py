
from io import BytesIO
from tempfile import SpooledTemporaryFile  
from transformers import DetrImageProcessor, DetrForObjectDetection
from PIL import Image, ImageDraw, ImageFont 
from typing import Annotated
from fastapi import Depends, UploadFile
from random import randint

import torch 
import os 
import warnings

from app.services.image.storage.local_storage import LocalImageStorage, get_local_image_storage  # Local storage service
from app.core.logging_config import get_logger

# Annotating dependencies for local storage
LocalImageStorageDep = Annotated[LocalImageStorage, Depends(get_local_image_storage)]

# Setting up logging for the ObjectDetectionService class
logger = get_logger("detection_service")

class ObjectDetectionService:
    """
    A service for performing object detection on images using the DETR model.
    
    @param local_storage: A service for saving and retrieving images from local storage.
    """
    def __init__(self, local_storage: LocalImageStorageDep):
        warnings.filterwarnings("ignore", category=UserWarning, module='torch')  # Ignore PyTorch warnings
        self.processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50")
        self.model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50", ignore_mismatched_sizes=True)
        self.confidence_threshold = 0.5 
        self.local_storage = local_storage
    
    def _get_font(self, size: int) -> ImageFont:
        """
        Returns a font for drawing text on the image.

        @param size: The size of the font.
        @return: An ImageFont object for text rendering.
        """
        try:
            return ImageFont.truetype("arial.ttf", size)
        except IOError:
            logger.warning("Arial font not found, using default font.")
            return ImageFont.load_default()

    def _get_random_colour(self) -> tuple[str, tuple[int, int, int]]:
        """
        Generates a random color in both hex and RGB formats.

        @return: A tuple containing the hex color code and the RGB tuple.
        """
        r, g, b = randint(0, 255), randint(0, 255), randint(0, 255)
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        return hex_color, (r, g, b)

    def _get_text_colour(self, rgb: tuple[int, int, int]) -> str:
        """
        Determines an appropriate text color (black or white) based on the background color brightness.

        @param rgb: The RGB color of the background.
        @return: A hex string representing either black or white, depending on the background brightness.
        """
        r, g, b = rgb
        brightness = (0.299 * r + 0.587 * g + 0.114 * b) / 255 
        return "#ffffff" if brightness < 0.5 else "#000000"  # Return black or white text based on brightness

    def _pillow_to_uploadfile(self, image: Image.Image, filename: str = "image.png") -> UploadFile:
        """
        Converts a Pillow image object to a FastAPI UploadFile.

        @param image: The image to convert.
        @param filename: The desired filename for the uploaded image.
        @return: An UploadFile object that can be used with FastAPI.
        """
        img_byte_arr = BytesIO()  # Create a byte stream for the image
        image.save(img_byte_arr, format=image.format or "PNG")  # Save image in memory
        img_byte_arr.seek(0)  # Reset byte stream pointer

        temp_file = SpooledTemporaryFile()  # Create a temporary file
        temp_file.write(img_byte_arr.read())  # Write the image bytes to the file
        temp_file.seek(0)  # Reset file pointer

        return UploadFile(filename=filename, file=temp_file)

    def get_bounding_boxes(self, image_path: str) -> str:
        """
        Detects objects in an image and draws bounding boxes around them.

        @param image_path: The path to the image on which to perform object detection.
        @return: The path to the new image with bounding boxes drawn on it.
        """
        image = Image.open(image_path)  
        image_copy = image.copy() 
        draw = ImageDraw.Draw(image_copy)  
        font = self._get_font(16)

        # Process the image with the DETR model
        inputs = self.processor(images=image, return_tensors="pt")
        outputs = self.model(**inputs)

        # Post-process the output and extract bounding boxes
        target_sizes = torch.tensor([image.size[::-1]])
        results = self.processor.post_process_object_detection(
            outputs, target_sizes=target_sizes, threshold=self.confidence_threshold
        )[0]

        # Draw bounding boxes and labels
        for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
            box = [round(coord) for coord in box.tolist()]  # Round the box coordinates
            x, y, x2, y2 = box 

            class_name = self.model.config.id2label[label.item()]
            confidence = score.item()

            # Generate random color for the bounding box and label text
            colour, rgb = self._get_random_colour()
            draw.rectangle([x, y, x2, y2], outline=colour, width=3) 

            # Prepare text and draw it
            text = f"{class_name}: {confidence:.2f}"
            text_bbox = draw.textbbox((x, y - 20), text, font=font)
            draw.rectangle(text_bbox, fill=colour)  # Draw background for text
            draw.text((x, y - 20), text, fill=self._get_text_colour(rgb), font=font)  # Draw text

        # Save the output image with bounding boxes drawn
        original_filename = os.path.basename(image_path)
        name, ext = os.path.splitext(original_filename)
        new_filename = f"{name}_bounding_boxes{ext}"

        output_path = self.local_storage.save(
            file=self._pillow_to_uploadfile(image_copy, filename=new_filename),
            folder="detected",
            filename=new_filename,
            format=image.format
        )
        
        logger.info(f"Bounding boxes saved to: {output_path}")
        return output_path 

    def get_detected_objects(self, image_path: str) -> list:
        """
        Detects objects in an image and returns the detected objects with their labels and confidence scores.

        @param image_path: The path to the image on which to perform object detection.
        @return: A list of dictionaries representing detected objects, each containing the label, confidence score, and bounding box.
        """
        image = Image.open(image_path)

        # Process the image with the DETR model
        inputs = self.processor(images=image, return_tensors="pt")
        outputs = self.model(**inputs)

        # Post-process the output and extract bounding boxes
        target_sizes = torch.tensor([image.size[::-1]])
        results = self.processor.post_process_object_detection(
            outputs, target_sizes=target_sizes, threshold=self.confidence_threshold
        )[0]

        detections = []
        for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
            detections.append({
                "label": self.model.config.id2label[label.item()],
                "confidence": score.item(), 
                "box": box.tolist()
            })
        
        logger.info(f"Detected {len(detections)} objects.")
        return detections 

def get_object_detection_service(local_storage: LocalImageStorageDep) -> ObjectDetectionService:
    """
    Dependency function to create an instance of ObjectDetectionService.

    @param local_storage: A service for saving and retrieving images from local storage.
    @return: An instance of the ObjectDetectionService class.
    """
    return ObjectDetectionService(local_storage=local_storage)
