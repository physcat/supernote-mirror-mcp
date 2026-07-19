"""Image processing for captured frames."""

from io import BytesIO

from PIL import Image


def frame_stats(png: bytes) -> str:
    """Describe a frame by its size and dominant pixel value; near 255 means a
    mostly-white screen (blank pages and standby alike)."""
    frame = Image.open(BytesIO(png)).convert("L")
    histogram = frame.histogram()
    dominant = histogram.index(max(histogram))
    return f"{frame.width}x{frame.height} pixels, dominant pixel value {dominant}"
