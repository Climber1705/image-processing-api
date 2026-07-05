from pathlib import Path


def build_display_filename(image_name: str, suffix: str | None = None) -> str:
    path = Path(image_name)
    stem = path.stem
    ext = path.suffix or ".jpg"
    if suffix:
        return f"{stem}_{suffix}{ext}"
    return f"{stem}{ext}"
