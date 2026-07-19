"""MCP server that captures the screen of a Supernote tablet via its built-in screencast."""

from importlib.metadata import version
from typing import Annotated

from mcpatom import Image, Server

from .capture import capture_frame
from .config import DEFAULT_PORT, config_file, load_config, state, write_config
from .image import INK_THRESHOLD, frame_stats, process


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
) -> Image | str:
    """Capture the Supernote screen as a PNG; pass any of x/y/w/h to capture
    just that region, and trimming (the default) crops the result to its ink,
    returning a text message instead when the captured area is blank. The
    screen is greyscale, 1404x1872 on some models (setup reports the actual
    size). Trimming assumes nothing about the UI: in the portrait notes app
    the toolbar may occupy the leftmost 100 columns and the status bar the
    bottom 82 rows, so excluding them with e.g. x=100, h=1790 can help
    there."""
    png = process(capture_frame(state.screencast_url), scale, auto_trim, threshold, x, y, w, h)
    if png is None:
        return "The captured area has no pixels darker than threshold; pass auto_trim=false for the image anyway"
    return Image(png, "image/png")


def main() -> None:
    load_config()
    server.serve_stdio()
