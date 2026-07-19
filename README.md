# supernote-mirror-mcp

MCP server that captures the screen of a Supernote tablet via its built-in
screencast.

Captures can be diffed, trimmed to the ink, cropped and scaled to keep vision
token usage down: a raw frame costs an LLM ~2500 tokens, a trimmed half-scale
capture of a few written lines ~70. Measured on an A6 X2 "Nomad" (1404x1872),
the only model this has been tested on; larger screens such as the Manta
(1920x2560) cost proportionally more.

## Prerequisites

- A Supernote tablet on the same Wi-Fi network, with screen mirroring enabled
  from the quick-access panel (swipe down from the top of the screen and tap
  the mirroring icon, beside the rotate icon). Enabling mirroring shows a
  dialog with the device's URL; it disappears at the first touch.
- [uv](https://docs.astral.sh/uv/), for `uvx`.

## Setup

With Claude Code:

```sh
claude mcp add supernote -- uvx supernote-mirror-mcp
```

For any other MCP client, register `uvx supernote-mirror-mcp` as a stdio
server. The command takes no arguments. With the standard JSON config:

```json
{
  "mcpServers": {
    "supernote": {
      "command": "uvx",
      "args": ["supernote-mirror-mcp"]
    }
  }
}
```

## Tools

- `setup` - updates or reports the configuration and checks the device
  connection.
- `capture_screen` - returns an image sized for an LLM to interpret
  directly. Supports optional region cropping (`x`/`y`/`w`/`h`) and an
  `auto_trim` that crops surrounding white space.
- `capture_changes` - returns the area that changed since the last capture.

## Configuration

On first use, call the `setup` tool with the address from the mirroring dialog
(`host`, plus `port` if not the default 8080); it applies the options and
reports whether the device is responding. The optional `save` parameter
writes the configuration to `config.json` in the platform config directory so
future sessions start connected.

## Licence

MIT
