<?php

declare(strict_types=1);

namespace EarlyForge\Pulse;

/**
 * Client for the EarlyForge Trends API.
 *
 * Covers 2 tiers under the same /v1/api/trends/* prefix:
 *   - Pulse mirror (free, any plan):
 *       GET /v1/api/trends/top
 *       GET /v1/api/trends/region/{region}
 *       GET /v1/api/trends/category/{category}
 *       GET /v1/api/trends/{trend_id}
 *   - Full trends feed (paid plans only — NOT "all trends unlocked", see
 *     fullTrends()):
 *       GET /v1/api/trends/full
 *       GET /v1/api/trends/full/{trend_id}
 *
 * Contract: docs/api/public-api-v1/openapi.yaml (repo root). This client
 * never sends a parameter the OpenAPI spec doesn't document.
 *
 * Zero-dependency on purpose: uses ext-curl rather than pulling in an
 * HTTP client library.
 */
final class PulseClient
{
    private const DEFAULT_BASE_URL = 'https://api.earlyforge.ai';
    private const TIMEOUT_SECONDS = 15;

    private readonly string $apiKey;
    private readonly string $baseUrl;

    /** @var (callable(string, array<string>): array{status: int, body: string})|null */
    private readonly ?\Closure $transport;

    /**
     * @param (callable(string, array<string>): array{status: int, body: string})|null $transport
     *   Override the HTTP transport (used by tests). Defaults to a real
     *   curl request.
     */
    public function __construct(
        string $apiKey,
        string $baseUrl = self::DEFAULT_BASE_URL,
        ?callable $transport = null,
    ) {
        if ($apiKey === '') {
            throw new \InvalidArgumentException('apiKey is required');
        }
        $this->apiKey = $apiKey;
        $this->baseUrl = rtrim($baseUrl, '/');
        $this->transport = $transport === null ? null : \Closure::fromCallable($transport);
    }

    /**
     * Global top trends — same daily snapshot as the Pulse homepage.
     *
     * @return array<string, mixed>
     */
    public function topTrends(?string $date = null, ?string $locale = null): array
    {
        return $this->get('/v1/api/trends/top', ['date' => $date, 'locale' => $locale]);
    }

    /**
     * Top trends for a region (ISO 3166-1 alpha-2, e.g. "US", "FR").
     *
     * @return array<string, mixed>
     */
    public function trendsByRegion(string $region, ?string $date = null, ?string $locale = null): array
    {
        return $this->get('/v1/api/trends/region/' . rawurlencode($region), [
            'date' => $date,
            'locale' => $locale,
        ]);
    }

    /**
     * Top trends for a category (e.g. "politics", "tech").
     *
     * @return array<string, mixed>
     */
    public function trendsByCategory(string $category, ?string $date = null, ?string $locale = null): array
    {
        return $this->get('/v1/api/trends/category/' . rawurlencode($category), [
            'date' => $date,
            'locale' => $locale,
        ]);
    }

    /**
     * Detail for one trend, including description, sources, and timeline.
     *
     * @return array<string, mixed>
     */
    public function getTrend(string $trendId): array
    {
        return $this->get('/v1/api/trends/' . rawurlencode($trendId));
    }

    /**
     * Full trends feed — paid plans only, and NOT "all trends unlocked".
     *
     * Every plan still reveals only a daily, random, category-diversified
     * budget of trend names (same budget the dashboard's Trends page shows
     * for this org today). Items outside that budget stay in the list but
     * with their name fields redacted (`name_locked: true`). A free-plan
     * key throws PulseApiException with statusCode 402 before this even
     * runs.
     *
     * @return array<string, mixed>
     */
    public function fullTrends(
        ?string $region = null,
        ?string $category = null,
        int $page = 1,
        int $limit = 20,
    ): array {
        return $this->get('/v1/api/trends/full', [
            'region' => $region,
            'category' => $category,
            'page' => (string) $page,
            'limit' => (string) $limit,
        ]);
    }

    /**
     * Full detail for one trend — paid plans only.
     *
     * Throws PulseApiException with statusCode 402 if the trend is outside
     * today's visible-name budget — same restriction the dashboard's own
     * detail panel enforces.
     *
     * @return array<string, mixed>
     */
    public function getFullTrend(string $trendId): array
    {
        return $this->get('/v1/api/trends/full/' . rawurlencode($trendId));
    }

    /**
     * @param array<string, string|null> $params
     * @return array<string, mixed>
     */
    private function get(string $path, array $params = []): array
    {
        $query = array_filter($params, static fn ($value) => $value !== null);
        $url = $this->baseUrl . $path;
        if ($query !== []) {
            $url .= '?' . http_build_query($query);
        }

        $headers = ['Authorization: Bearer ' . $this->apiKey];
        $response = $this->transport !== null
            ? ($this->transport)($url, $headers)
            : $this->curlGet($url, $headers);

        if ($response['status'] >= 400) {
            $detail = null;
            $decoded = json_decode($response['body'], true);
            if (is_array($decoded) && isset($decoded['detail'])
                && (is_string($decoded['detail']) || is_array($decoded['detail']))) {
                $detail = $decoded['detail'];
            }
            throw new PulseApiException(
                sprintf('EarlyForge API returned HTTP %d for %s', $response['status'], $url),
                $response['status'],
                $detail,
            );
        }

        $decoded = json_decode($response['body'], true);
        if (!is_array($decoded)) {
            throw new PulseApiException('EarlyForge API returned a non-JSON response for ' . $url);
        }

        return $decoded;
    }

    /**
     * @param array<string> $headers
     * @return array{status: int, body: string}
     */
    private function curlGet(string $url, array $headers): array
    {
        $handle = curl_init($url);
        if ($handle === false) {
            throw new PulseApiException('Could not initialize cURL for ' . $url);
        }

        curl_setopt($handle, CURLOPT_HTTPHEADER, $headers);
        curl_setopt($handle, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($handle, CURLOPT_TIMEOUT, self::TIMEOUT_SECONDS);

        $body = curl_exec($handle);
        if ($body === false) {
            $error = curl_error($handle);
            curl_close($handle);
            throw new PulseApiException("Could not reach EarlyForge API at {$url}: {$error}");
        }

        $status = (int) curl_getinfo($handle, CURLINFO_HTTP_CODE);
        curl_close($handle);

        return ['status' => $status, 'body' => (string) $body];
    }
}
