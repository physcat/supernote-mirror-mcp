"""Image processing for captured frames."""

from io import BytesIO

from PIL import Image, ImageChops

INK_THRESHOLD = 240  # e-ink white reads near 255; anything darker counts as ink
TRIM_PAD = 10

_baseline: Image.Image | None = None  # the frame remembered by the previous capture_changes


def decode(png: bytes) -> Image.Image:
    return Image.open(BytesIO(png)).convert("L")


def remember(frame: Image.Image) -> Image.Image | None:
    """Swap the cached baseline for frame, returning the previous baseline."""
    global _baseline
    previous, _baseline = _baseline, frame
    return previous


def changed_bbox(a: Image.Image, b: Image.Image) -> tuple[int, int, int, int] | None:
    """Bbox of the pixels differing between two same-size frames, padded by
    TRIM_PAD; None when the frames are identical."""
    bbox = ImageChops.difference(a, b).getbbox()
    if bbox is None:
        return None
    left, top, right, bottom = bbox
    return (
        max(left - TRIM_PAD, 0),
        max(top - TRIM_PAD, 0),
        min(right + TRIM_PAD, a.width),
        min(bottom + TRIM_PAD, a.height),
    )


def frame_stats(png: bytes) -> str:
    """Describe a frame by its size and dominant pixel value; near 255 means a
    mostly-white screen (blank pages and standby alike)."""
    frame = decode(png)
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
) -> tuple[bytes, tuple[int, int, int, int]] | None:
    """Crop then scale a frame, returning a PNG together with the box of the
    frame it shows, in unscaled frame coordinates. Passing any of x/y/w/h
    crops to that region first (unspecified edges default to the frame's
    own); trimming then crops to the ink darker than threshold, or yields
    None when the captured area has no such ink. A region outside the frame,
    or empty, is an error: Pillow would silently pad it with ink-black
    instead."""
    frame = decode(png)
    left = top = 0
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
        bbox = _ink_bbox(frame, threshold)
        if bbox is None:
            return None
        frame = frame.crop(bbox)
        left, top = left + bbox[0], top + bbox[1]
    box = (left, top, left + frame.width, top + frame.height)
    if scale != 1:
        size = (max(1, round(frame.width * scale)), max(1, round(frame.height * scale)))
        frame = frame.resize(size, Image.Resampling.LANCZOS)
    buf = BytesIO()
    frame.save(buf, "PNG")
    return buf.getvalue(), box


def _ink_bbox(frame: Image.Image, threshold: int) -> tuple[int, int, int, int] | None:
    """Box of the frame's ink, padded by TRIM_PAD; None for a frame with no
    ink."""
    bbox = frame.point(lambda p: p < threshold).getbbox()
    if bbox is None:
        return None
    left, top, right, bottom = bbox
    return (
        max(left - TRIM_PAD, 0),
        max(top - TRIM_PAD, 0),
        min(right + TRIM_PAD, frame.width),
        min(bottom + TRIM_PAD, frame.height),
    )
