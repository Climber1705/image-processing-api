from abc import ABC, abstractmethod
from fastapi import UploadFile


class BaseImageValidator(ABC):
    @abstractmethod
    def validate(self, image: UploadFile) -> None:
        pass
