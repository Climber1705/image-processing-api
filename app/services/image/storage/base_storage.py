from abc import ABC, abstractmethod
from typing import Optional
from fastapi import UploadFile


class BaseImageStorage(ABC):
    @abstractmethod
    def save(
        self,
        file: UploadFile,
        folder: Optional[str] = None,
        filename: Optional[str] = None,
        format: Optional[str] = "JPEG",
    ) -> str:
        pass

    @abstractmethod
    def get_url(self, filename: str) -> str:
        pass

    @abstractmethod
    def delete(self, directory: str, filename: str) -> bool:
        pass
