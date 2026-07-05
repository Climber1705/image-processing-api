from io import BytesIO
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from app.vision.domain.errors import CorruptImageError, InvalidInputError


def _open_rgb(source: Path | BytesIO, label: str) -> Image.Image:
    try:
        with Image.open(source) as img:
            img.verify()
    except (UnidentifiedImageError, OSError, SyntaxError) as exc:
        raise CorruptImageError(f"Image file is corrupt or unreadable: {label}") from exc

    try:
        with Image.open(source) as img:
            if img.width <= 0 or img.height <= 0:
                raise CorruptImageError(f"Image has invalid dimensions: {label}")
            return img.convert("RGB")
    except CorruptImageError:
        raise
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise CorruptImageError(f"Image file is corrupt or unreadable: {label}") from exc


def load_from_path(path: Path) -> Image.Image:
    if not path.exists():
        raise InvalidInputError(f"Image {path.name} not found")
    if path.stat().st_size == 0:
        raise CorruptImageError(f"Image file is empty: {path.name}")
    return _open_rgb(path, path.name)


def load_from_bytes(data: bytes, label: str) -> Image.Image:
    if not data:
        raise CorruptImageError(f"Image file is empty: {label}")
    return _open_rgb(BytesIO(data), label)
