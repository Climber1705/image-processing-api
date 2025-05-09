from pydantic import BaseModel, Field 
from typing import Optional, List  

# Model to represent a request to rotate an image with specific parameters
class RotateEditRequest(BaseModel):
    """
    Represents a request to rotate an image by a certain number of degrees, optionally expanding the canvas.
    
    Attributes:
        degrees (float): The number of degrees to rotate the image.
        expand (Optional[bool]): Whether to expand the canvas to fit the rotated image. Defaults to False.
    """
    degrees: float = Field(..., description="Degrees to rotate")
    expand: Optional[bool] = False 

# Model to represent a request to sharpen an image with specific parameters
class SharpenEditRequest(BaseModel):
    """
    Represents a request to sharpen an image with specific parameters.
    
    Attributes:
        factor (float): The sharpening factor, must be greater than 0. Default is 1.5.
        radius (float): The radius of the sharpening effect, must be greater than 0. Default is 2.0.
        threshold (int): The threshold for sharpening, must be greater than or equal to 0. Default is 2.
    """
    factor: float = Field(1.5, gt=0)
    radius: float = Field(2.0, gt=0) 
    threshold: int = Field(2, ge=0)  

