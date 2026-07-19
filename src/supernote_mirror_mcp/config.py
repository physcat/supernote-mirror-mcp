import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PORT = 8080
SCREENCAST_PATH = "/screencast.mjpeg"


@dataclass
class State:
    host: str | None = None
    port: int = DEFAULT_PORT

    @property
    def screencast_url(self) -> str:
        if self.host is None:
            raise ValueError(f"No Supernote host configured: call setup, or set host in {config_file()}")
        return f"http://{self.host}:{self.port}{SCREENCAST_PATH}"


state = State()


def config_file() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME", "")
    if xdg.strip():
        base = Path(xdg)
    elif sys.platform == "win32":
        base = Path(os.environ["APPDATA"])
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".config"
    return base / "supernote-mirror-mcp" / "config.json"


def load_config() -> None:
    try:
        data = json.loads(config_file().read_text())
    except FileNotFoundError:
        return
    state.host = data.get("host", state.host)
    state.port = data.get("port", state.port)


def write_config() -> None:
    path = config_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"host": state.host, "port": state.port}, indent=2) + "\n")
