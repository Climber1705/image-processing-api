from app.editing.api.responses import EditResponse
from app.editing.domain.dtos import EditResultDTO


def to_edit_response(result: EditResultDTO) -> EditResponse:
    return EditResponse(path=result.path)
