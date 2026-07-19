from test_image import screen, size_of

import supernote_mirror_mcp as snm
from supernote_mirror_mcp import image


def test_capture_changes_baseline_diff_no_change_and_erasure_paths(monkeypatch):
    monkeypatch.setattr(snm.state, "host", "10.0.0.1")
    monkeypatch.setattr(image, "_baseline", None)
    inked = screen((300, 500, 320, 510))
    more = screen((300, 500, 320, 510), (600, 700, 640, 720))
    frames = iter([inked, more, more, screen()])
    monkeypatch.setattr(snm, "capture_frame", lambda url: next(frames))

    first = snm.capture_changes(scale=1)
    assert isinstance(first, tuple)  # no baseline: the full screen, trimmed to its ink
    assert first[1] == {"x": 290, "y": 490, "w": 40, "h": 30, "scale": 1, "screen_w": 1404, "screen_h": 1872}

    second = snm.capture_changes(scale=1)
    assert isinstance(second, tuple)
    changed, meta = second
    assert size_of(changed.data) == (60, 40)
    assert meta == {"x": 590, "y": 690, "w": 60, "h": 40, "scale": 1, "screen_w": 1404, "screen_h": 1872}

    assert snm.capture_changes(scale=1) == "No change since the previous capture"

    erased = snm.capture_changes(scale=1)  # everything wiped: the changed area has no ink left
    assert isinstance(erased, str)
    assert "(290, 490) to (650, 730)" in erased and "erasure" in erased


def test_capture_screen_seeds_the_changes_baseline(monkeypatch):
    monkeypatch.setattr(snm.state, "host", "10.0.0.1")
    monkeypatch.setattr(image, "_baseline", None)
    frames = iter([screen(), screen((300, 500, 320, 510))])
    monkeypatch.setattr(snm, "capture_frame", lambda url: next(frames))

    snm.capture_screen(auto_trim=False)
    result = snm.capture_changes(scale=1)
    assert isinstance(result, tuple)
    assert size_of(result[0].data) == (20 + 2 * image.TRIM_PAD, 10 + 2 * image.TRIM_PAD)
