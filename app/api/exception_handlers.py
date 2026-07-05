from fastapi import Request
from fastapi.responses import JSONResponse

from app.media.errors import MediaDomainError


async def media_domain_error_handler(_request: Request, exc: MediaDomainError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})
