# earlyforge-pulse-sdk

JavaScript/TypeScript client for the **EarlyForge Trends API**, with two
tiers under the same `/v1/api/trends/*` prefix:

- **Pulse mirror** — free on every account, no plan required. An
  authenticated mirror of the free, anonymous trend data already shown on
  [pulse.earlyforge.ai](https://pulse.earlyforge.ai): same daily snapshot,
  same trend count, same fields.
- **Full trends feed** — paid plans only, and **not "all trends
  unlocked."** Every plan reveals a bigger, but still limited, daily,
  random, category-diversified budget of trend names — exactly what your
  organization's dashboard Trends page shows unlocked today, no more, no
  less. See `fullTrends()` below.

This is **not** a client for articles, briefs, or alerts — the public API
never exposes those on any plan. Uses the global `fetch`, so it works in
Node 18+ and in browsers with no other dependency.

Full reference: [docs.earlyforge.ai/guides/api/javascript-sdk](https://docs.earlyforge.ai/guides/api/javascript-sdk). Source: [github.com/Earlyforge-official/earlyforge](https://github.com/Earlyforge-official/earlyforge/tree/main/sdk-js-earlyforge).

## Install

Not published to npm yet. Contact [support@earlyforge.ai](mailto:support@earlyforge.ai) for early access.

## Quickstart

### ESM

```ts
import { PulseClient } from "earlyforge-pulse-sdk"

const client = new PulseClient("ef_live_xxxxxxxxxxxxxxxx")
const snapshot = await client.topTrends({ locale: "fr" })
console.log(snapshot.trends[0])
```

### CommonJS

```js
const { PulseClient } = await import("earlyforge-pulse-sdk")
const client = new PulseClient("ef_live_xxxxxxxxxxxxxxxx")
const snapshot = await client.topTrends()
```

(The package ships ESM-only — a CommonJS `require()` consumer loads it
via a dynamic `import()`, as shown above.)

Get a key from **Settings → API Keys** in the EarlyForge console — any
account works, Pulse access is free.

## Methods

### `topTrends({ date?, locale? })`

Global top trends — same snapshot as the Pulse homepage.

```ts
const { trends, total, cached_at, cache_ttl_seconds } = await client.topTrends()
// trends[0] => {
//   trend_id: "tr_a1b2c3",
//   display_name: "AI regulation",
//   region: "US",
//   language: "en",
//   categories: ["politics"],
//   global_score: 87.5,
//   lifecycle_stage: "growing",
//   detected_at: "2026-11-04T08:00:00Z",
//   hours_since_detection: 6.2,
//   velocity_zscore: 2.1,
//   acceleration: 0.4,
//   n_sources: 12,
//   source_diversity: 0.8,
//   cross_lingual_root: false,
//   google_trends_lead_hours: null,
//   topic_class: null,
//   entities: [],
//   description: null
// }
```

### `trendsByRegion(region, { date?, locale? })`

Top trends for an ISO 3166-1 alpha-2 region code (e.g. `"US"`, `"FR"`).
Same `TrendList` shape as `topTrends`.

### `trendsByCategory(category, { date?, locale? })`

Top trends for a category (e.g. `"politics"`, `"tech"`). Same
`TrendList` shape as `topTrends`.

### `getTrend(trendId)`

Detail for one trend. Same fields as a trend, plus `canonical_name`,
`sources`, a full `description`, and a `timeline` of `{ts, score,
sources_count}` points.

### `fullTrends({ region?, category?, page?, limit? })`

**Paid plans only.** A bigger, paginated slice of the trend corpus than
the fixed Pulse snapshot — gated by the same daily random name-visibility
budget as the dashboard. Items outside today's budget stay in the list
with their name fields redacted (`name_locked: true`), not removed.

```ts
const { items, total, page, per_page } = await client.fullTrends({ limit: 50 })
// items[1] => { trend_id: "tr_d4e5f6", display_name: "••••••••••", name_locked: true, ... }
```

A free-plan key rejects with `PulseApiError` (`statusCode === 402`,
`detail.error === "upgrade_required"`) before this even runs.

### `getFullTrend(trendId)`

**Paid plans only.** Full detail for one trend — same TD-sourced fields
as the dashboard's detail panel (`topsis_score`, `editorial_title`, etc.).
Rejects with `PulseApiError` (`statusCode === 402`,
`detail.code === "trend_locked"`) if the trend is outside today's
visible-name budget.

## Errors

Every non-2xx response rejects with a `PulseApiError` carrying
`statusCode` and `detail` (mirroring the OpenAPI spec's `401`
missing/invalid/revoked key, `404` unknown trend, and `502` upstream
unavailable responses). Network failures also reject with
`PulseApiError`.

```ts
import { PulseApiError } from "earlyforge-pulse-sdk"

try {
  await client.getTrend("does-not-exist")
} catch (error) {
  if (error instanceof PulseApiError) {
    console.error(error.statusCode, error.detail)
  }
}
```

## Rate limits

No monthly call quota on this surface, for any plan — only the shared
60 requests/60s burst limit applies, same as the anonymous Pulse page.

## Tests

```bash
npm run build && npm test
```
