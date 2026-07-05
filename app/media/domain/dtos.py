from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FileMetadataDTO:
    filename: str
    format: str
    mode: str
    width: int
    height: int
    size_bytes: int
    path: str
    url: str | None = None


@dataclass(frozen=True, slots=True)
class ImageDTO:
    id: str
    filename: str
    format: str
    mode: str
    width: int
    height: int
    size_bytes: int
    path: str
    folder: str
    url: str | None = None


@dataclass(frozen=True, slots=True)
class SaveImageResultDTO:
    path: str
    image: ImageDTO


@dataclass(frozen=True, slots=True)
class DeleteImageResultDTO:
    status: str
    message: str
    deleted_image: ImageDTO


@dataclass(frozen=True, slots=True)
class OperationStatusDTO:
    status: str
    message: str
