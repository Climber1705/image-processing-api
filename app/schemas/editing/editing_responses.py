from pydantic import BaseModel


class EditResponse(BaseModel):
    path: str
