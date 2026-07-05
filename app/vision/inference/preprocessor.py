from PIL import Image


def load_image(image_path: str) -> Image.Image:
    return Image.open(image_path).convert("RGB")


def resize_if_needed(image: Image.Image, max_dimension: int) -> Image.Image:
    width, height = image.size
    if width <= max_dimension and height <= max_dimension:
        return image

    scale = max_dimension / max(width, height)
    new_size = (int(width * scale), int(height * scale))
    return image.resize(new_size, Image.Resampling.LANCZOS)


def preprocess(
    image: Image.Image,
    processor,
    device: str,
    max_dimension: int | None = None,
) -> dict:
    if max_dimension is not None:
        image = resize_if_needed(image, max_dimension)

    inputs = processor(images=image, return_tensors="pt")
    return {key: value.to(device) for key, value in inputs.items()}
