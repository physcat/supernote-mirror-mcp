"""Single-frame capture from the screencast stream.

Despite the .mjpeg path, the device serves multipart/x-mixed-replace PNG
frames; a capture reads just enough of the endless stream to cut out the
first complete PNG, wherever the chunk boundaries fall."""

import urllib.request
from collections.abc import Iterable

from .config import config_file

FRAME_TIMEOUT = 10.0


def extract_png(chunks: Iterable[bytes]) -> bytes:
    """Return the first complete PNG (signature through the IEND CRC) found in
    a stream of byte chunks."""
    buf = bytearray()
    for chunk in chunks:
        buf += chunk
        start = buf.find(b"\x89PNG")
        end = buf.find(b"IEND", start) if start >= 0 else -1
        if end >= 0 and end + 8 <= len(buf):
            return bytes(buf[start : end + 8])
    raise ValueError("The screencast stream ended without a complete PNG frame")


def capture_frame(url: str, timeout: float = FRAME_TIMEOUT) -> bytes:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return extract_png(iter(lambda: response.read(65536), b""))
    except OSError as e:
        raise ConnectionError(
            f"Cannot reach the Supernote at {url} ({e}): check the device's Wi-Fi and"
            " screen mirroring (swipe down from the top of its screen, tap the mirroring"
            f" icon), or call setup to fix the address (config file: {config_file()})"
        ) from e
