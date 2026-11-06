# earlyforge/pulse-sdk

PHP client for the **EarlyForge Trends API**, with two tiers under the
same `/v1/api/trends/*` prefix:

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
never exposes those on any plan. Zero dependencies: uses `ext-curl`
directly rather than pulling in an HTTP client library.

Full reference: [docs.earlyforge.ai/guides/api/php-sdk](https://docs.earlyforge.ai/guides/api/php-sdk).

## Install

Not published to Packagist yet. Contact [support@earlyforge.ai](mailto:support@earlyforge.ai) for early access.

## Quickstart

```php
use EarlyForge\Pulse\PulseClient;

$client = new PulseClient('ef_live_xxxxxxxxxxxxxxxx');

$snapshot = $client->topTrends(null, 'fr');
echo $snapshot['trends'][0]['display_name'];
```

Get a key from **Settings → API Keys** in the EarlyForge console — any
account works, Pulse access is free.

## Methods

### `topTrends(?string $date = null, ?string $locale = null): array`

Global top trends — same snapshot as the Pulse homepage. Returns
`['trends' => [...], 'total' => int, 'cached_at' => string,
'cache_ttl_seconds' => int]`.

### `trendsByRegion(string $region, ?string $date = null, ?string $locale = null): array`

Top trends for an ISO 3166-1 alpha-2 region code (e.g. `"US"`, `"FR"`).
Same shape as `topTrends()`.

### `trendsByCategory(string $category, ?string $date = null, ?string $locale = null): array`

Top trends for a category (e.g. `"politics"`, `"tech"`). Same shape as
`topTrends()`.

### `getTrend(string $trendId): array`

Detail for one trend. Same fields as a trend, plus `canonical_name`,
`sources`, a full `description`, and a `timeline` of `{ts, score,
sources_count}` points.

### `fullTrends(?string $region = null, ?string $category = null, int $page = 1, int $limit = 20): array`

**Paid plans only.** A bigger, paginated slice of the trend corpus than
the fixed Pulse snapshot — gated by the same daily random name-visibility
budget as the dashboard. Items outside today's budget stay in the list
with their name fields redacted (`'name_locked' => true`), not removed.
Returns `['items' => [...], 'total' => int, 'page' => int, 'per_page' => int]`.

A free-plan key throws `PulseApiException` with `getStatusCode() === 402`
and `getDetail()['error'] === 'upgrade_required'` before this even runs.

### `getFullTrend(string $trendId): array`

**Paid plans only.** Full detail for one trend — same TD-sourced fields
as the dashboard's detail panel (`topsis_score`, `editorial_title`, etc.).
Throws `PulseApiException` with `getStatusCode() === 402` and
`getDetail()['code'] === 'trend_locked'` if the trend is outside today's
visible-name budget.

## Errors

Every non-2xx response throws `EarlyForge\Pulse\PulseApiException` with
`getStatusCode()` and `getDetail()` (mirroring the OpenAPI spec's `401`
missing/invalid/revoked key, `404` unknown trend, and `502` upstream
unavailable responses). `getDetail()` is a plain string on the Pulse
endpoints, but a structured array (`['error' => ..., 'code' => ...]`) on
the full-trends 402s — check `is_array()` before using it. Network/cURL
failures also throw `PulseApiException`.

```php
use EarlyForge\Pulse\PulseApiException;

try {
    $client->getTrend('does-not-exist');
} catch (PulseApiException $e) {
    echo $e->getStatusCode() . ': ' . $e->getDetail();
}
```

## Rate limits

No monthly call quota on this surface, for any plan — only the shared
60 requests/60s burst limit applies, same as the anonymous Pulse page.

## Tests

```bash
composer install
composer test
```
