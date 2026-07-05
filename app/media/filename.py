from pathlib import Path

def get_display_filename(
    filename: str | None,
    original_filename: str | None,
    extension: str,
) -> str: 
    if filename:
        return f"{Path(filename).stem}{extension}"
    if original_filename:
        original = Path(original_filename)
        return f"{original.stem}{extension}"
    return f"image{extension}"