"""MCP server that captures the screen of a Supernote tablet via its built-in screencast."""

import urllib.request
from importlib.metadata import version

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


server = Server("supernote-mirror", version=version("supernote-mirror-mcp"))


@server.tool()
def setup(host: str | None = None, port: int = DEFAULT_PORT, save: bool | None = None) -> str:
    """Configure the server and check the device connection; with no arguments,
    reports the current configuration. Passing host applies the Supernote's
    address, host plus port (the port applies only alongside a host). save=True
    writes the config file for future sessions, save=False leaves it alone, and
    the default updates an existing config file only when the address changed."""
    previous = (state.host, state.port)
    if host is not None:
        state.host = host
        state.port = port
    url = state.screencast_url  # before any write: a hostless save must fail, not persist
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
