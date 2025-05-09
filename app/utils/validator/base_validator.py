from abc import ABC, abstractmethod
from fastapi import UploadFile

class BaseImageValidator(ABC):
    """
    Abstract base class for validating image files.
    
    This class defines the structure for image validation logic. Subclasses should implement
    the `validate` method to provide their own image validation logic.
    """

    @abstractmethod
    def validate(self, image: UploadFile) -> None:
        """
        Validate the given image file.

        @param image: The image file to be validated, provided as an `UploadFile` instance from FastAPI.

        """
        pass # This method should be implemented by subclasses to enforce specific validation rules.
