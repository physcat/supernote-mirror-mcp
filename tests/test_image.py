from io import BytesIO

import pytest
from PIL import Image

from supernote_mirror_mcp import image


def to_png(frame: Image.Image) -> bytes:
    buf = BytesIO()
    frame.save(buf, "PNG")
    return buf.getvalue()


def screen(*ink_boxes: tuple[int, int, int, int]) -> bytes:
    """A white full-size frame with black rectangles at the given boxes."""
    frame = Image.new("L", (1404, 1872), 255)
    for box in ink_boxes:
        frame.paste(0, box)
    return to_png(frame)


def size_of(png: bytes | None) -> tuple[int, int]:
    assert png is not None
    return Image.open(BytesIO(png)).size


def test_frame_stats_reports_size_and_dominant_value():
    frame = Image.new("L", (3, 2))
    frame.putdata([254, 254, 254, 0, 0, 30])
    assert image.frame_stats(to_png(frame)) == "3x2 pixels, dominant pixel value 254"


def test_trim_crops_to_padded_ink():
    png = image.process(screen((300, 500, 320, 510)), scale=1, auto_trim=True)
    assert size_of(png) == (20 + 2 * image.TRIM_PAD, 10 + 2 * image.TRIM_PAD)


def test_untrimmed_region_is_exact_scaled_and_defaults_missing_edges():
    png = image.process(screen(), scale=0.5, auto_trim=False, x=100, y=200, w=50, h=40)
    assert size_of(png) == (25, 20)
    png = image.process(screen(), scale=1, auto_trim=False, x=1000)
    assert size_of(png) == (404, 1872)


def test_region_outside_the_frame_is_an_error():
    with pytest.raises(ValueError, match="1404x1872"):
        image.process(screen(), scale=1, auto_trim=True, x=1300, w=200)
    with pytest.raises(ValueError, match="does not fit"):
        image.process(screen(), scale=1, auto_trim=True, x=100, w=0)


def test_trim_applies_within_a_region():
    png = image.process(screen((300, 500, 320, 510)), scale=1, auto_trim=True, x=250, y=450, w=200, h=200)
    assert size_of(png) == (20 + 2 * image.TRIM_PAD, 10 + 2 * image.TRIM_PAD)


def test_threshold_sets_the_ink_cutoff():
    frame = Image.new("L", (1404, 1872), 255)
    frame.paste(250, (300, 500, 320, 510))
    assert image.process(to_png(frame), scale=1, auto_trim=True) is None  # 250 is not ink by default
    png = image.process(to_png(frame), scale=1, auto_trim=True, threshold=252)
    assert size_of(png) == (20 + 2 * image.TRIM_PAD, 10 + 2 * image.TRIM_PAD)
