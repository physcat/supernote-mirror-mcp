from io import BytesIO

from PIL import Image

from supernote_mirror_mcp.image import frame_stats


def png(width: int, height: int, pixels: list[int]) -> bytes:
    frame = Image.new("L", (width, height))
    frame.putdata(pixels)
    buf = BytesIO()
    frame.save(buf, "PNG")
    return buf.getvalue()


def test_frame_stats_reports_size_and_dominant_value():
    assert frame_stats(png(3, 2, [254, 254, 254, 0, 0, 30])) == "3x2 pixels, dominant pixel value 254"
