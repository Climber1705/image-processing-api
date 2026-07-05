from random import randint

from PIL import Image, ImageDraw, ImageFont

from app.core.logging_config import get_logger
from app.services.inference.schemas import Detection

logger = get_logger("visualizer")


def _get_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except IOError:
        logger.warning("Arial font not found, using default font.")
        return ImageFont.load_default()


def _random_colour() -> tuple[str, tuple[int, int, int]]:
    r, g, b = randint(0, 255), randint(0, 255), randint(0, 255)
    return f"#{r:02x}{g:02x}{b:02x}", (r, g, b)


def _text_colour(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    brightness = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#ffffff" if brightness < 0.5 else "#000000"


def draw_bounding_boxes(image: Image.Image, detections: list[Detection]) -> Image.Image:
    image_copy = image.copy()
    draw = ImageDraw.Draw(image_copy)
    font = _get_font(16)

    for detection in detections:
        box = [round(coord) for coord in detection.box]
        x, y, x2, y2 = box

        colour, rgb = _random_colour()
        draw.rectangle([x, y, x2, y2], outline=colour, width=3)

        text = f"{detection.label}: {detection.confidence:.2f}"
        text_bbox = draw.textbbox((x, y - 20), text, font=font)
        draw.rectangle(text_bbox, fill=colour)
        draw.text((x, y - 20), text, fill=_text_colour(rgb), font=font)

    return image_copy
