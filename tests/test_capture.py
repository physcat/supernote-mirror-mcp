import pytest

from supernote_mirror_mcp import capture

FRAME = b"\x89PNG\r\n\x1a\nIHDR-and-IDAT-data" + b"IEND" + b"\x00\x01\x02\x03"
PREAMBLE = b"--frame\r\nContent-Type: image/png\r\n\r\n"


def test_signature_arriving_mid_chunk():
    assert capture.extract_png([PREAMBLE + FRAME[:2], FRAME[2:], b"--frame\r\n"]) == FRAME


def test_iend_split_across_chunks():
    assert capture.extract_png([PREAMBLE + FRAME[:-6], FRAME[-6:]]) == FRAME


def test_stream_ending_without_a_complete_frame():
    with pytest.raises(ValueError, match="without a complete PNG frame"):
        capture.extract_png([PREAMBLE + FRAME[:-1]])


def test_connection_error_names_setup_and_the_config_file(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    with pytest.raises(ConnectionError, match="setup") as excinfo:
        capture.capture_frame("http://127.0.0.1:9/", timeout=1)
    assert str(capture.config_file()) in str(excinfo.value)
