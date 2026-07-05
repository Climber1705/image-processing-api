from enum import StrEnum


class ImageFolder(StrEnum):
    UPLOADED = "uploaded"
    EDITED = "edited"
    DETECTED = "detected"

    @classmethod
    def values(cls) -> list[str]:
        return [member.value for member in cls]

    @classmethod
    def get_folder_names(cls, folder: str) -> list[str]:
        if folder == FolderFilter.ALL:
            return cls.values()
        return [folder]


class FolderFilter(StrEnum):
    UPLOADED = "uploaded"
    EDITED = "edited"
    DETECTED = "detected"
    ALL = "all"

    @classmethod
    def values(cls) -> list[str]:
        return [member.value for member in cls]
