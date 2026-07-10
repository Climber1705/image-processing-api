from pydantic import BaseModel, Field


class RotateEditRequest(BaseModel):
    degrees: float = Field(..., description="Degrees to rotate")
    expand: bool | None = False


class SharpenEditRequest(BaseModel):
    factor: float = Field(1.5, gt=0)
    radius: float = Field(2.0, gt=0)
    threshold: int = Field(2, ge=0)
