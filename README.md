# supernote-mirror-mcp

MCP server that captures the screen of a Supernote tablet via its built-in
screencast.

## Prerequisites

- A Supernote tablet reachable on the local network, with screencast enabled
  under Settings > Security & Privacy > Screen Mirroring.
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

- `setup` - set the tablet's address and check the connection.
- `capture_screen` - capture the current screen as a PNG image.

## Configuration

On first use, call the `setup` tool with the tablet's address (`host`, plus
`port` if not the default 8080); it applies the options and reports whether the
device is responding. The optional `save` parameter writes the configuration to
`config.json` in the platform config directory so future sessions start
connected.

## Licence

MIT
