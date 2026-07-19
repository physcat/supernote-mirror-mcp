import json
import sys
from pathlib import Path

import pytest

import supernote_mirror_mcp as snm
from supernote_mirror_mcp import config


@pytest.fixture(autouse=True)
def isolated_state(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setattr(config.state, "host", None)
    monkeypatch.setattr(config.state, "port", config.DEFAULT_PORT)
    monkeypatch.setattr(snm, "_probe", lambda url: f"Screencast URL is {url} (device responding)")


@pytest.mark.parametrize(
    ("xdg", "platform", "base"),
    [
        ("/xdg", "win32", Path("/xdg")),
        (" ", "darwin", Path.home() / "Library" / "Application Support"),
        (None, "win32", Path("/appdata")),
        (None, "linux", Path.home() / ".config"),
    ],
)
def test_config_file_platform_resolution(monkeypatch, xdg, platform, base):
    if xdg is None:
        monkeypatch.delenv("XDG_CONFIG_HOME")
    else:
        monkeypatch.setenv("XDG_CONFIG_HOME", xdg)
    monkeypatch.setenv("APPDATA", "/appdata")
    monkeypatch.setattr(sys, "platform", platform)
    assert config.config_file() == base / "supernote-mirror-mcp" / "config.json"


def test_load_config_reads_host_and_port():
    path = config.config_file()
    path.parent.mkdir(parents=True)
    path.write_text('{"host": "10.0.0.5", "port": 9090}')
    config.load_config()
    assert config.state == config.State("10.0.0.5", 9090)


def test_setup_applies_host_and_port():
    result = snm.setup("10.0.0.5", port=9090, save=False)
    assert config.state == config.State("10.0.0.5", 9090)
    assert "http://10.0.0.5:9090/screencast.mjpeg" in result
    snm.setup("10.0.0.5", save=False)
    assert config.state.port == 8080  # omitting the port resets it to the default


def test_setup_save_semantics():
    snm.setup("10.0.0.1")
    assert not config.config_file().exists()  # default with no file: no write
    snm.setup("10.0.0.2", save=True)
    snm.setup("10.0.0.3", save=False)
    assert json.loads(config.config_file().read_text()) == {"host": "10.0.0.2", "port": 8080}
    snm.setup("10.0.0.4")  # default with a file: writes the change
    assert json.loads(config.config_file().read_text())["host"] == "10.0.0.4"
    config.config_file().write_text('{"host": "canary"}')
    snm.setup("10.0.0.4")  # nothing changed: no write
    assert snm.setup() == "Screencast URL is http://10.0.0.4:8080/screencast.mjpeg (device responding)"
    assert json.loads(config.config_file().read_text())["host"] == "canary"


def test_hostless_setup_reports_guidance_without_writing():
    result = snm.setup(save=True)
    assert "mirroring icon" in result
    assert str(config.config_file()) in result
    assert not config.config_file().exists()


def test_no_host_error_names_setup_and_the_config_file():
    with pytest.raises(ValueError, match="setup") as excinfo:
        _ = config.state.screencast_url
    assert str(config.config_file()) in str(excinfo.value)
