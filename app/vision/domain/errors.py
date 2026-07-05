class VisionDomainError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ModelNotReadyError(VisionDomainError): ...


class CorruptImageError(VisionDomainError): ...


class InferenceError(VisionDomainError): ...
