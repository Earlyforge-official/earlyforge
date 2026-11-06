# earlyforge-trends MCP server

Wraps the [EarlyForge Trends API](https://docs.earlyforge.ai/guides/api/trends-api)
as MCP tools so an AI agent can query EarlyForge's trend data directly,
across both tiers of the `/v1/api/trends/*` prefix.

**Pulse mirror** — free, any account, no plan required. An authenticated,
verbatim mirror of the free, anonymous data already shown on
pulse.earlyforge.ai — same daily snapshot, same trend count, same fields,
nothing more:

- `top_trends(date?, locale?)` — same snapshot as the Pulse homepage.
- `trends_by_region(region, date?, locale?)`
- `trends_by_category(category, date?, locale?)`
- `get_trend(trend_id)` — same payload as the public trend detail page.

**Full trends feed** — paid plans only, and **not "all trends
unlocked."** Every plan reveals a bigger, but still limited, daily,
random, category-diversified budget of trend names — exactly what the
organization's dashboard Trends page shows unlocked today, no more, no
less. A trend outside that budget comes back name-redacted (list) or
locked (detail):

- `full_trends(region?, category?, page?, limit?)`
- `get_full_trend(trend_id)`

These 6 tools need an `EARLYFORGE_API_KEY` (free Pulse access, any
account — see below; `full_trends`/`get_full_trend` additionally need a
paid plan on that key's organization). Two more tools need **no account
or API key at all**:

- `list_docs()` — the full EarlyForge documentation index (titles + URLs).
- `read_docs()` — the entire documentation, concatenated.

Both just read the public `docs.earlyforge.ai/llms.txt` /
`llms-full.txt` routes — the same ones a browser or any other agent
can fetch directly, no sign-up required.

It also exposes an MCP **prompt**, `editorial_watch(country?, sector?)`, that
walks an agent through building a trend-watch briefing with the tools above,
and tells it to be upfront if the user asks for something beyond this free
tier (real-time monitoring, the full country/category catalog) — pointing to
earlyforge.ai/pricing rather than inventing capabilities.

This server runs **locally only**, as a stdio process you launch yourself —
there is no cloud-hosted `https://mcp.earlyforge.ai` endpoint (yet). Every
config below starts the same local Python script; the only thing that
differs is which client file it goes in.

## Requirements

- Any EarlyForge account (Pulse access is free, no paid plan required)
  and an API key from **Settings → API Keys** in the EarlyForge
  console. Keys look like `ef_live_xxxxxxxxxxxxxxxx` and are shown once
  at creation.
- Python 3.10+.

## Install

```bash
cd tools/mcp-earlyforge
pip install -r requirements.txt
```

## Configure

| Env var | Required | Default |
|---|---|---|
| `EARLYFORGE_API_KEY` | yes | — |
| `EARLYFORGE_API_BASE` | no | `https://api.earlyforge.ai` |

## Run standalone

```bash
EARLYFORGE_API_KEY=ef_live_xxx python server.py
```

## Add to Claude

### Claude Code

One-liner (local stdio server, env var passed with `--env`):

```bash
claude mcp add earlyforge-trends --env EARLYFORGE_API_KEY=ef_live_xxxxxxxxxxxxxxxx -- python /absolute/path/to/tools/mcp-earlyforge/server.py
```

- Use `-s project` instead of the default `-s local` to share the entry
  via `.mcp.json` with everyone who clones this repo (don't commit your
  real key if you do — use a placeholder and let each teammate set
  their own `EARLYFORGE_API_KEY`).
- Verify it's registered: `claude mcp list` / `claude mcp get earlyforge-trends`.
- Remove it: `claude mcp remove earlyforge-trends`.

### Claude Desktop

Add this block to `claude_desktop_config.json` (Settings → Developer →
Edit Config):

```json
{
  "mcpServers": {
    "earlyforge-trends": {
      "command": "python",
      "args": ["/absolute/path/to/tools/mcp-earlyforge/server.py"],
      "env": {
        "EARLYFORGE_API_KEY": "ef_live_xxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

Restart Claude Desktop after editing the file.

### Cursor

Add this to `.cursor/mcp.json` (project-level) or your global Cursor MCP
config — same shape as Claude Desktop's:

```json
{
  "mcpServers": {
    "earlyforge-trends": {
      "command": "python",
      "args": ["/absolute/path/to/tools/mcp-earlyforge/server.py"],
      "env": {
        "EARLYFORGE_API_KEY": "ef_live_xxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

### VS Code (MCP extension) / other stdio-capable clients

Any client that supports a local stdio MCP server takes the same three
pieces of information: `command: python`, `args: ["/absolute/path/to/
tools/mcp-earlyforge/server.py"]`, and the `EARLYFORGE_API_KEY` env var.
Consult your client's docs for where that JSON block goes.

## Error handling

A revoked/disabled key, an unknown `trend_id`, and a temporarily
unavailable Pulse upstream are all surfaced as plain tool-call error
messages (not stack traces) — see `server.py::_get` for the mapping
from the OpenAPI spec's documented 401 / 404 / 502 responses. On
`full_trends`/`get_full_trend`, a 402 is also surfaced as a plain error:
either "requires a paid plan" (free-plan key) or "outside today's
visible-name budget" (`trend_locked`). The Pulse mirror has no monthly
quota (it's free, cached data), so there's no quota-exhaustion case to
handle there.
