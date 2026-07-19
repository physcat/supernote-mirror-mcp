"""MCP server that captures the screen of a Supernote tablet via its built-in screencast."""

from importlib.metadata import version
from typing import Annotated

from mcpatom import Image, Server

from .capture import capture_frame
from .config import DEFAULT_PORT, config_file, load_config, state, write_config
from .image import INK_THRESHOLD, changed_bbox, decode, frame_stats, process, remember


def _metadata(box: tuple[int, int, int, int], scale: float, screen: tuple[int, int]) -> dict:
    """The screen region an image shows, in unscaled screen coordinates."""
    left, top, right, bottom = box
    return {
        "x": left,
        "y": top,
        "w": right - left,
        "h": bottom - top,
        "scale": scale,
        "screen_w": screen[0],
        "screen_h": screen[1],
    }


def _probe(url: str) -> str:
    try:
        return f"Screencast URL is {url} ({frame_stats(capture_frame(url, timeout=3))})"
    except (OSError, ValueError) as e:  # capture errors carry their own guidance
        return str(e)


server = Server(
    "supernote-mirror",
    version=version("supernote-mirror-mcp"),
    instructions=(
        "Captures the screen of a Supernote tablet over Wi-Fi. First run: with the"
        " device's Wi-Fi on, swipe down from the top of its screen and tap the"
        " mirroring icon (beside the rotate icon); a dialog then shows the device's"
        " URL. Ask the user to read it off and call setup with it."
    ),
)


@server.tool()
def setup(
    host: Annotated[str | None, "the address the Supernote displays when enabling screen mirroring"] = None,
    port: Annotated[int, "the screencast port, shown alongside the address"] = DEFAULT_PORT,
    save: bool | None = None,
) -> str:
    """Configure the server and check the device connection by capturing a
    frame; the report gives the frame's size and dominant pixel value (near 255
    means a mostly-white screen, blank pages and standby alike). With no
    arguments, reports the current configuration, or first-run guidance while
    no host is set. Passing host applies the Supernote's address, host plus
    port (the port applies only alongside a host). save=True writes the config
    file for future sessions, save=False leaves it alone, and the default
    updates an existing config file only when the address changed."""
    previous = (state.host, state.port)
    if host is not None:
        state.host = host
        state.port = port
    if state.host is None:  # nothing to probe or save: explain how to get an address
        return (
            "No host configured. Turn on the Supernote's Wi-Fi, then swipe down from"
            " the top of its screen and tap the mirroring icon (beside the rotate"
            " icon): a dialog shows the device's URL, e.g."
            f" http://192.168.1.101:{DEFAULT_PORT}. It disappears at the first touch;"
            " toggling mirroring off and on shows it again. Ask the user to read it"
            f" off the device, then call setup with it. Config file: {config_file()}"
        )
    url = state.screencast_url
    if save is None:
        save = (state.host, state.port) != previous and config_file().exists()
    if save:
        write_config()
    return _probe(url)


@server.tool()
def capture_screen(
    scale: Annotated[float, "resize factor applied after cropping; the default keeps handwriting legible"] = 0.5,
    auto_trim: Annotated[bool, "crop to the ink in the captured area"] = True,
    threshold: Annotated[int, "greyscale level below which a pixel counts as ink for auto trim"] = INK_THRESHOLD,
    x: Annotated[int | None, "left edge of an exact region to capture"] = None,
    y: Annotated[int | None, "top edge of the region"] = None,
    w: Annotated[int | None, "width of the region"] = None,
    h: Annotated[int | None, "height of the region"] = None,
) -> tuple[Image, dict] | str:
    """Capture the Supernote screen as a PNG; pass any of x/y/w/h to capture
    just that region, and trimming (the default) crops the result to its ink,
    returning a text message instead when the captured area is blank. Images
    come with metadata giving the screen region shown (x/y/w/h in unscaled
    screen coordinates), the scale, and the screen size. The screen is
    greyscale, 1404x1872 on some models. Trimming assumes nothing about the
    UI: in the portrait notes app the toolbar may occupy the leftmost 100
    columns and the status bar the bottom 82 rows, so excluding them with
    e.g. x=100, h=1790 can help there. Also refreshes the baseline
    capture_changes diffs against."""
    full = capture_frame(state.screencast_url)
    frame = decode(full)
    remember(frame)
    result = process(full, scale, auto_trim, threshold, x, y, w, h)
    if result is None:
        return "The captured area has no pixels darker than threshold; pass auto_trim=false for the image anyway"
    png, box = result
    return Image(png, "image/png"), _metadata(box, scale, frame.size)


@server.tool()
def capture_changes(
    scale: Annotated[float, "resize factor applied to the changed region"] = 0.5,
    auto_trim: Annotated[bool, "crop to the ink in the changed area"] = True,
    threshold: Annotated[int, "greyscale level below which a pixel counts as ink for auto trim"] = INK_THRESHOLD,
) -> tuple[Image, dict] | str:
    """Capture only what changed on the Supernote screen since the previous
    capture (capture_screen or capture_changes): an image of the changed
    region plus the same metadata block capture_screen returns, or a message
    when nothing changed. With no prior capture to diff against, the full
    screen. An erasure can leave the changed area without ink; the message
    then gives the area so capture_screen can inspect it."""
    png = capture_frame(state.screencast_url)
    frame = decode(png)
    previous = remember(frame)
    changed = None
    if previous is not None and previous.size == frame.size:  # else no baseline, or the screen rotated
        changed = changed_bbox(previous, frame)
        if changed is None:
            return "No change since the previous capture"
    left, top, right, bottom = changed if changed else (0, 0, frame.width, frame.height)
    result = process(png, scale, auto_trim, threshold, x=left, y=top, w=right - left, h=bottom - top)
    if result is None:
        return (
            f"The changed area ({left}, {top}) to ({right}, {bottom}) now has no ink darker than"
            " threshold, probably an erasure"
        )
    cropped, box = result
    return Image(cropped, "image/png"), _metadata(box, scale, frame.size)


def main() -> None:
    load_config()
    server.serve_stdio()
