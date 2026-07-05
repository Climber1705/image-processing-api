class MediaDomainError(Exception):
    status_code: int = 500

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ImageNotFoundError(MediaDomainError):
    status_code = 404


class DuplicateImageError(MediaDomainError):
    status_code = 409


class InvalidFolderError(MediaDomainError):
    status_code = 400


class InvalidMoveError(MediaDomainError):
    status_code = 400


class ImageConflictError(MediaDomainError):
    status_code = 409


class ImageSaveError(MediaDomainError):
    status_code = 500


class ImageOperationError(MediaDomainError):
    status_code = 500


class ImageCreationError(MediaDomainError):
    status_code = 409
