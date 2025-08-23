from PIL import Image, UnidentifiedImageError

def extract_image_meta(path: str) -> tuple[str, dict]:
    """
    Returns ("", meta) because we don't OCR yet.
    Meta includes width/height/format; text is empty.
    """
    try:
        with Image.open(path) as im:
            meta = {"format": im.format, "mode": im.mode, "size": {"width": im.width, "height": im.height}}
            return "", meta
    except (FileNotFoundError, UnidentifiedImageError):
        return "", {"error": "unreadable image"}
