# earlyforge-cli

Command-line client for the **EarlyForge Trends API**, with two tiers
under the same `/v1/api/trends/*` prefix:

- **Pulse mirror** (`pulse top|region|category|trend`) — free on every
  account, no plan required. The same daily snapshot already shown on
  [pulse.earlyforge.ai](https://pulse.earlyforge.ai).
- **Full trends feed** (`pulse full`/`pulse full-trend`) — paid plans
  only, and **not "all trends unlocked."** Every plan reveals a bigger,
  but still limited, daily, random, category-diversified budget of trend
  names — exactly what your organization's dashboard Trends page shows
  unlocked today, no more, no less.

Not a CLI for articles, briefs, or alerts — the public API never exposes
those on any plan. Full reference: [docs.earlyforge.ai/guides/api/cli](https://docs.earlyforge.ai/guides/api/cli).

## Install

Not published yet. Contact [support@earlyforge.ai](mailto:support@earlyforge.ai) for early access.

## Configure

```bash
export EARLYFORGE_API_KEY=ef_live_xxxxxxxxxxxxxxxx
```

Get a key from **Settings → API Keys** in the EarlyForge console. Or pass
`--api-key` on each command instead of the env var.

## Commands

```bash
earlyforge pulse top [--date YYYY-MM-DD] [--locale fr]
earlyforge pulse region <REGION> [--date YYYY-MM-DD] [--locale fr]
earlyforge pulse category <CATEGORY> [--date YYYY-MM-DD] [--locale fr]
earlyforge pulse trend <TREND_ID>
earlyforge pulse full [--region US] [--category tech] [--page 1] [--limit 20]
earlyforge pulse full-trend <TREND_ID>
```

Every command pretty-prints the JSON response and accepts `--api-key` and
`--base-url` (default `https://api.earlyforge.ai`, useful for pointing at
a local gateway in development).

`pulse full` and `pulse full-trend` require a paid-plan API key — a
free-plan key gets HTTP 402. They are **not** "all trends unlocked":
every plan, paid included, only reveals a daily, random,
category-diversified budget of trend names, same as the dashboard's
Trends page. A trend outside that budget stays in the list with its name
redacted (`"name_locked": true`) for `pulse full`, or returns HTTP 402
for `pulse full-trend`.

### Examples

```bash
earlyforge pulse top
earlyforge pulse top --locale fr --date 2026-11-01
earlyforge pulse region US
earlyforge pulse category politics
earlyforge pulse trend tr_a1b2c3
earlyforge pulse full --region US --limit 50
earlyforge pulse full-trend tr_a1b2c3
```

## Errors

A non-2xx response prints `Error: ... (<detail>)` to stderr and exits
with status `1` — the same `401` invalid-key / `404` unknown-trend /
`502` upstream-unavailable cases documented in the OpenAPI spec, plus
`402` (`upgrade_required` on `pulse full`/`pulse full-trend` for a
free-plan key, `trend_locked` on `pulse full-trend` for a trend outside
today's budget).

## Rate limits

No monthly call quota on this surface — only the shared 60 requests/60s
burst limit applies, same as the anonymous Pulse page.

## Tests

```bash
pip install -e . pytest
pytest
```
