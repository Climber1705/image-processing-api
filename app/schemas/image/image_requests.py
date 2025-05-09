from pydantic import BaseModel, Field

# Model to represent the request for moving an image from one folder to another
class MoveImageRequest(BaseModel):
    """
    Represents a request to move an image from one folder to another.
    
    Attributes:
        source_folder (str): The name of the current folder where the image is located.
        target_folder (str): The name of the folder where the image should be moved to.
    """
    source_folder: str = Field("uploaded", description="Current folder name")
    target_folder: str = Field("edited", description="Target folder name")
