
from pydantic import BaseModel
from typing import List

# Define a model for a single detection box (bounding box) in an image
class DetectionBox(BaseModel):
    """
    Represents a detection box, including the label, confidence score, and the coordinates of the bounding box.
    
    Attributes:
        label (str): The label or name of the detected object.
        confidence (float): The confidence score of the detection (between 0 and 1).
        box (list): The coordinates of the bounding box in the image (usually in the format [x_min, y_min, x_max, y_max]).
    """
    label: str 
    confidence: float  
    box: list  

# Define a response model for bounding box results, including the path to the image and detection details
class BoundingBoxResponse(BaseModel):
    """
    Represents the response structure for bounding box detection.
    
    Attributes:
        message (str): A message providing additional details about the detection.
        image_path (str): The path to the image file on which detection was performed.
        detections (List[DetectionBox]): A list of DetectionBox objects representing detected objects in the image.
    """
    message: str
    image_path: str 
    detections: List[DetectionBox] 

# Define a response model for detected objects, with a simpler response structure
class DetectedObjectsResponse(BaseModel):
    """
    Represents the response structure for detected objects in an image.
    
    Attributes:
        message (str): A message providing additional details about the detections.
        detected_objects (List[DetectionBox]): A list of DetectionBox objects representing detected objects in the image.
    """
    message: str
    detected_objects: List[DetectionBox]
