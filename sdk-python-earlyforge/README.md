# earlyforge (Python)

Python client for the **EarlyForge Trends API**, with two tiers under the
same `/v1/api/trends/*` prefix:

- **Pulse mirror** — free on every account, no plan required. An
  authenticated mirror of the free, anonymous trend data already shown on
  [pulse.earlyforge.ai](https://pulse.earlyforge.ai): same daily snapshot,
  same trend count, same fields, no extra filters.
- **Full trends feed** — paid plans only, and **not "all trends
  unlocked."** Every plan reveals a bigger, but still limited, daily,
  random, category-diversified budget of trend names — exactly what your
  organization's dashboard Trends page shows unlocked today, no more, no
  less. See `full_trends()` below.

This is **not** a client for articles, briefs, or alerts — the public API
never exposes those on any plan.

Full reference: [docs.earlyforge.ai/guides/api/python-sdk](https://docs.earlyforge.ai/guides/api/python-sdk).

## Install

Not published to PyPI yet. Contact [support@earlyforge.ai](mailto:support@earlyforge.ai) for early access.

## Quickstart

```python
from earlyforge import PulseClient

client = PulseClient(api_key="ef_live_xxxxxxxxxxxxxxxx")

snapshot = client.top_trends(locale="fr")
print(snapshot["trends"][0]["display_name"])
```

Get a key from **Settings → API Keys** in the EarlyForge console — any
account works, Pulse access is free.

## Methods

### `top_trends(date=None, locale=None)`

Global top trends — same snapshot as the Pulse homepage.

```python
client.top_trends()
# {
#   "trends": [
#     {
#       "trend_id": "tr_a1b2c3",
#       "display_name": "AI regulation",
#       "region": "US",
#       "language": "en",
#       "categories": ["politics"],
#       "global_score": 87.5,
#       "lifecycle_stage": "growing",
#       "detected_at": "2026-11-04T08:00:00Z",
#       "hours_since_detection": 6.2,
#       "velocity_zscore": 2.1,
#       "acceleration": 0.4,
#       "n_sources": 12,
#       "source_diversity": 0.8,
#       "cross_lingual_root": false,
#       "google_trends_lead_hours": null,
#       "topic_class": null,
#       "entities": [],
#       "description": None
#     }
#   ],
#   "total": 20,
#   "cached_at": "2026-11-04T06:00:00Z",
#   "cache_ttl_seconds": 3600
# }
```

### `trends_by_region(region, date=None, locale=None)`

Top trends for an ISO 3166-1 alpha-2 region code (e.g. `"US"`, `"FR"`).
Same `TrendList` shape as `top_trends`.

### `trends_by_category(category, date=None, locale=None)`

Top trends for a category (e.g. `"politics"`, `"tech"`). Same `TrendList`
shape as `top_trends`.

### `get_trend(trend_id)`

Detail for one trend. Same fields as a `Trend`, plus `canonical_name`,
`sources`, a full `description`, and a `timeline` of `{ts, score,
sources_count}` points.

```python
client.get_trend("tr_a1b2c3")
```

### `full_trends(region=None, category=None, page=1, limit=20)`

**Paid plans only.** A bigger, paginated slice of the trend corpus than
the fixed Pulse snapshot — gated by the same daily random name-visibility
budget as the dashboard. Items outside today's budget stay in the list
with their name fields redacted (`name_locked: true`), not removed.

```python
client.full_trends(limit=50)
# {
#   "items": [
#     {"trend_id": "tr_a1b2c3", "display_name": "Ransomware wave", ...},
#     {"trend_id": "tr_d4e5f6", "display_name": "••••••••••", "name_locked": True, ...}
#   ],
#   "total": 2,
#   "page": 1,
#   "per_page": 50
# }
```

A free-plan key raises `PulseApiError` with `status_code=402` and
`detail={"error": "upgrade_required", ...}` before this even runs.

### `get_full_trend(trend_id)`

**Paid plans only.** Full detail for one trend — same TD-sourced fields
as the dashboard's detail panel (`topsis_score`, `editorial_title`, etc.).
Raises `PulseApiError` with `status_code=402` and
`detail={"code": "trend_locked", ...}` if the trend is outside today's
visible-name budget.

```python
client.get_full_trend("tr_a1b2c3")
```

## Errors

Every non-2xx response raises `earlyforge.PulseApiError` with
`status_code` and `detail` attributes (mirroring the OpenAPI spec's `401`
missing/invalid/revoked key, `404` unknown trend, and `502` upstream
unavailable responses). Network failures (DNS, timeout, connection
refused) also raise `PulseApiError`.

```python
from earlyforge import PulseApiError

try:
    client.get_trend("does-not-exist")
except PulseApiError as exc:
    print(exc.status_code, exc.detail)
```

## Rate limits

No monthly call quota on this surface, for any plan — only the shared
60 requests/60s burst limit applies, same as the anonymous Pulse page.

## Tests

```bash
pip install -e . pytest
pytest
```
