"""Image processing for captured frames."""

from io import BytesIO

from PIL import Image

INK_THRESHOLD = 240  # e-ink white reads near 255; anything darker counts as ink
TRIM_PAD = 10


def frame_stats(png: bytes) -> str:
    """Describe a frame by its size and dominant pixel value; near 255 means a
    mostly-white screen (blank pages and standby alike)."""
    frame = Image.open(BytesIO(png)).convert("L")
    histogram = frame.histogram()
    dominant = histogram.index(max(histogram))
    return f"{frame.width}x{frame.height} pixels, dominant pixel value {dominant}"


def process(
    png: bytes,
    scale: float,
    auto_trim: bool,
    threshold: int = INK_THRESHOLD,
    x: int | None = None,
    y: int | None = None,
    w: int | None = None,
    h: int | None = None,
) -> bytes | None:
    """Crop then scale a frame, returning a PNG. Passing any of x/y/w/h crops
    to that region first (unspecified edges default to the frame's own);
    trimming then crops to the ink darker than threshold, or yields None when
    the captured area has no such ink. A region outside the frame, or empty,
    is an error: Pillow would silently pad it with ink-black instead."""
    frame = Image.open(BytesIO(png)).convert("L")
    if (x, y, w, h) != (None, None, None, None):
        left = 0 if x is None else x
        top = 0 if y is None else y
        right = frame.width if w is None else left + w
        bottom = frame.height if h is None else top + h
        if not (0 <= left < right <= frame.width and 0 <= top < bottom <= frame.height):
            raise ValueError(
                f"Region ({left}, {top}) to ({right}, {bottom}) does not fit the {frame.width}x{frame.height} frame"
            )
        frame = frame.crop((left, top, right, bottom))
    if auto_trim:
        trimmed = _trimmed(frame, threshold)
        if trimmed is None:
            return None
        frame = trimmed
    if scale != 1:
        size = (max(1, round(frame.width * scale)), max(1, round(frame.height * scale)))
        frame = frame.resize(size, Image.Resampling.LANCZOS)
    buf = BytesIO()
    frame.save(buf, "PNG")
    return buf.getvalue()


def _trimmed(frame: Image.Image, threshold: int) -> Image.Image | None:
    """Crop to the frame's ink, padded by TRIM_PAD; None for a frame with no
    ink."""
    bbox = frame.point(lambda p: p < threshold).getbbox()
    if bbox is None:
        return None
    left, top, right, bottom = bbox
    return frame.crop(
        (
            max(left - TRIM_PAD, 0),
            max(top - TRIM_PAD, 0),
            min(right + TRIM_PAD, frame.width),
            min(bottom + TRIM_PAD, frame.height),
        )
    )
