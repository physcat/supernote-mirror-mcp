"""MCP server that captures the screen of a Supernote tablet via its built-in screencast."""

import urllib.request
from importlib.metadata import version
from typing import Annotated

from mcpatom import Image, Server

from .capture import capture_frame
from .config import DEFAULT_PORT, config_file, load_config, state, write_config


def _probe(url: str) -> str:
    # urlopen returns once the headers arrive; closing before any frame is read
    try:
        with urllib.request.urlopen(url, timeout=3):
            return "device responding"
    except OSError as e:
        return f"device not responding: {e}"


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
    """Configure the server and check the device connection; with no arguments,
    reports the current configuration, or first-run guidance while no host is
    set. Passing host applies the Supernote's address, host plus port (the port
    applies only alongside a host). save=True writes the config file for future
    sessions, save=False leaves it alone, and the default updates an existing
    config file only when the address changed."""
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
    return f"Screencast URL is {url} ({_probe(url)})"


@server.tool()
def capture_screen() -> Image:
    """Capture the current Supernote screen as a full-resolution PNG image."""
    return Image(capture_frame(state.screencast_url), "image/png")


def main() -> None:
    load_config()
    server.serve_stdio()
