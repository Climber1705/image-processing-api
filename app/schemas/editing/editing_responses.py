
from pydantic import BaseModel 
from typing import List

# Model to represent the response after applying a single image edit
class EditResponse(BaseModel):
    """
    Represents the response after applying an edit to a single image.
    
    Attributes:
        path (str): The file path to the edited image.
    """
    path: str

