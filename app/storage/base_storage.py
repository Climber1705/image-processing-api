from typing import BinaryIO
from abc import ABC, abstractmethod


class BaseImageStorage(ABC):
    @abstractmethod
    def save(self, file: BinaryIO, folder: str | None = None, filename: str | None = None, format: str = "JPEG") -> str:
        pass

    @abstractmethod
    def get(self, filename: str) -> BinaryIO:
        pass

    @abstractmethod
    def delete(self, filename: str) -> bool:
        pass
