from pathlib import Path

from app.media.domain.errors import InvalidFilenameError


def sanitize_filename(name: str) -> str:
    cleaned = Path(name).name.strip()
    if not cleaned or cleaned in {".", ".."} or "/" in cleaned or "\\" in cleaned:
        raise InvalidFilenameError(f"Invalid filename: {name!r}")
    if "\x00" in cleaned:
        raise InvalidFilenameError(f"Invalid filename: {name!r}")
    return cleaned


def get_display_filename(
    filename: str | None,
    original_filename: str | None,
    extension: str,
) -> str:
    if filename:
        stem = Path(sanitize_filename(filename)).stem
        return f"{stem}{extension}"
    if original_filename:
        stem = Path(sanitize_filename(original_filename)).stem
        return f"{stem}{extension}"
    return f"image{extension}"


def build_display_filename(image_name: str, suffix: str | None = None) -> str:
    safe_name = sanitize_filename(image_name)
    path = Path(safe_name)
    stem = path.stem
    ext = path.suffix or ".jpg"
    if suffix:
        return f"{stem}_{suffix}{ext}"
    return f"{stem}{ext}"
