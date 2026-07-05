from pydantic import BaseModel, Field


class MoveImageRequest(BaseModel):
    source_folder: str = Field("uploaded", description="Current folder name")
    target_folder: str = Field("edited", description="Target folder name")
