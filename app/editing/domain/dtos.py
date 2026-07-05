from dataclasses import dataclass

from app.media.domain.dtos import ImageDTO


@dataclass(frozen=True, slots=True)
class EditResultDTO:
    path: str
    image: ImageDTO
