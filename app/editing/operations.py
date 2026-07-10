from PIL import Image, ImageEnhance, ImageFilter, ImageOps


def resize(img: Image.Image, width: int, height: int) -> Image.Image:
    return img.resize((width, height), Image.LANCZOS)


def grayscale(img: Image.Image) -> Image.Image:
    return ImageOps.grayscale(img)


def rotate(img: Image.Image, degrees: int, expand: bool = False) -> Image.Image:
    return img.rotate(degrees, expand=expand, resample=Image.BICUBIC)


def blur(img: Image.Image, radius: float = 2.0) -> Image.Image:
    return img.filter(ImageFilter.GaussianBlur(radius))


def sharpen(
    img: Image.Image,
    factor: float = 2.0,
    radius: float = 2.0,
    threshold: int = 3,
) -> Image.Image:
    return img.filter(
        ImageFilter.UnsharpMask(
            radius=radius,
            percent=int(factor * 100),
            threshold=threshold,
        )
    )


def adjust_brightness(img: Image.Image, factor: float) -> Image.Image:
    return ImageEnhance.Brightness(img).enhance(factor)


def adjust_contrast(img: Image.Image, factor: float) -> Image.Image:
    return ImageEnhance.Contrast(img).enhance(factor)
