<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/brand/earlyforge-lockup-dark.svg">
    <img src="assets/brand/earlyforge-lockup-light.svg" alt="EarlyForge" width="280">
  </picture>
</p>

<p align="center">
  <b>Real-time trend intelligence API, SDKs, CLI, and MCP server.</b><br>
  Official client libraries for the <a href="https://docs.earlyforge.ai/guides/api/trends-api">EarlyForge Trends API</a>.
</p>

<p align="center">
  <a href="./LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
  <a href="https://docs.earlyforge.ai/guides/api">
    <img alt="Docs" src="https://img.shields.io/badge/docs-docs.earlyforge.ai-6C5CE7">
  </a>
  <a href="https://earlyforge.ai/pricing">
    <img alt="Free tier" src="https://img.shields.io/badge/pulse%20tier-free-00B894">
  </a>
  <a href="https://modelcontextprotocol.io">
    <img alt="MCP" src="https://img.shields.io/badge/MCP-compatible-5B91F4">
  </a>
</p>

---

EarlyForge tracks trending topics across 100+ connectors (news, social, search, academic, government) and scores them for genuine emergence — not just raw volume. This repo has everything you need to pull that data into your own code or AI agent: official SDKs, a CLI, and an MCP server for Claude, ChatGPT, Gemini, and other MCP-compatible agents.

## Packages

| Package | Language | Status |
| --- | --- | --- |
| [`sdk-python-earlyforge`](./sdk-python-earlyforge) | Python | Not yet published to PyPI |
| [`sdk-js-earlyforge`](./sdk-js-earlyforge) | JavaScript/TypeScript | Not yet published to npm |
| [`sdk-php-earlyforge`](./sdk-php-earlyforge) | PHP | Not yet published to Packagist |
| [`cli-earlyforge`](./cli-earlyforge) | Python (CLI) | Not yet published to PyPI |
| [`mcp-earlyforge`](./mcp-earlyforge) | Python (local MCP server) | Install from this repo |

Each package has its own README with install, quickstart, and the full method/command list.

## MCP — two ways to connect

- **Remote connector** (Claude.ai, ChatGPT, Gemini, or any client that supports adding a remote MCP server by URL): add `https://api.earlyforge.ai/mcp` — sign in with your EarlyForge account via OAuth, no install, no API key to paste. See the [MCP guide](https://docs.earlyforge.ai/guides/api/mcp#remote-connector).
- **Local stdio server** (Claude Code, Claude Desktop, Cursor): run [`mcp-earlyforge`](./mcp-earlyforge) from this repo with an API key. See its [README](./mcp-earlyforge/README.md).

## Getting an API key

Create a free account at [earlyforge.ai](https://earlyforge.ai), then generate a key from **Settings → API Keys**. Pulse access (top trends, by region, by category) is free on every plan, no card required. A paid plan additionally unlocks the full trends feed.

## Full documentation

**[docs.earlyforge.ai/guides/api](https://docs.earlyforge.ai/guides/api)** — API reference, rate limits, error codes, and framework-specific guides.

## Contributing

Issues and pull requests are welcome — see [CONTRIBUTING.md](./CONTRIBUTING.md).

## License

MIT — see [LICENSE](./LICENSE).
