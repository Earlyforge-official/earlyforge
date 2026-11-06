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
 * Uses the global `fetch` — works in Node 18+ and in browsers.
 */

const DEFAULT_BASE_URL = "https://api.earlyforge.ai"

export interface PulseClientOptions {
  baseUrl?: string
}

export interface TrendListResponse {
  trends: Record<string, unknown>[]
  total: number
  cached_at: string
  cache_ttl_seconds: number
}

export interface TrendDetailResponse extends Record<string, unknown> {
  trend_id: string
  canonical_name: string
  sources: string[]
  description: string
  timeline: { ts: string; score: number; sources_count: number }[]
}

export interface FullTrendListResponse {
  items: Record<string, unknown>[]
  total: number
  page: number
  per_page: number
}

export interface FullTrendDetailResponse extends Record<string, unknown> {
  trend_id: string
  display_name: string
  region: string
  language: string
  categories: string[]
  entities: { label: string; type: string; qid: string | null }[]
  global_score: number
  status: string
  started_at: string
  last_seen_at: string
}

export class PulseApiError extends Error {
  readonly statusCode?: number
  readonly detail?: unknown

  constructor(message: string, options?: { statusCode?: number; detail?: unknown }) {
    super(message)
    this.name = "PulseApiError"
    this.statusCode = options?.statusCode
    this.detail = options?.detail
  }
}

export class PulseClient {
  private readonly apiKey: string
  private readonly baseUrl: string

  constructor(apiKey: string, options: PulseClientOptions = {}) {
    if (!apiKey) {
      throw new Error("apiKey is required")
    }
    this.apiKey = apiKey
    this.baseUrl = (options.baseUrl ?? DEFAULT_BASE_URL).replace(/\/$/, "")
  }

  private async get<T>(path: string, params: Record<string, string | undefined> = {}): Promise<T> {
    const url = new URL(`${this.baseUrl}${path}`)
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined) url.searchParams.set(key, value)
    }

    let response: Response
    try {
      response = await fetch(url, {
        headers: { Authorization: `Bearer ${this.apiKey}` },
      })
    } catch (error) {
      throw new PulseApiError(`Could not reach EarlyForge API at ${url.toString()}: ${String(error)}`)
    }

    if (!response.ok) {
      let detail: unknown
      try {
        const body = (await response.json()) as { detail?: unknown }
        detail = body.detail
      } catch {
        detail = undefined
      }
      throw new PulseApiError(
        `EarlyForge API returned HTTP ${response.status} for ${url.toString()}`,
        { statusCode: response.status, detail },
      )
    }

    return (await response.json()) as T
  }

  /** Global top trends — same daily snapshot as the Pulse homepage. */
  topTrends(options: { date?: string; locale?: string } = {}): Promise<TrendListResponse> {
    return this.get<TrendListResponse>("/v1/api/trends/top", options)
  }

  /** Top trends for a region (ISO 3166-1 alpha-2, e.g. "US", "FR"). */
  trendsByRegion(
    region: string,
    options: { date?: string; locale?: string } = {},
  ): Promise<TrendListResponse> {
    return this.get<TrendListResponse>(`/v1/api/trends/region/${encodeURIComponent(region)}`, options)
  }

  /** Top trends for a category (e.g. "politics", "tech"). */
  trendsByCategory(
    category: string,
    options: { date?: string; locale?: string } = {},
  ): Promise<TrendListResponse> {
    return this.get<TrendListResponse>(`/v1/api/trends/category/${encodeURIComponent(category)}`, options)
  }

  /** Detail for one trend, including description, sources, and timeline. */
  getTrend(trendId: string): Promise<TrendDetailResponse> {
    return this.get<TrendDetailResponse>(`/v1/api/trends/${encodeURIComponent(trendId)}`)
  }

  /**
   * Full trends feed — paid plans only, and NOT "all trends unlocked".
   *
   * Every plan still reveals only a daily, random, category-diversified
   * budget of trend names (same budget the dashboard's Trends page shows
   * for this org today). Items outside that budget stay in the list but
   * with their name fields redacted (`name_locked: true`). A free-plan key
   * throws `PulseApiError` with `statusCode === 402` before this even runs.
   */
  fullTrends(
    options: { region?: string; category?: string; page?: number; limit?: number } = {},
  ): Promise<FullTrendListResponse> {
    return this.get<FullTrendListResponse>("/v1/api/trends/full", {
      region: options.region,
      category: options.category,
      page: options.page?.toString(),
      limit: options.limit?.toString(),
    })
  }

  /**
   * Full detail for one trend — paid plans only.
   *
   * Throws `PulseApiError` with `statusCode === 402` if the trend is
   * outside today's visible-name budget — same restriction the
   * dashboard's own detail panel enforces.
   */
  getFullTrend(trendId: string): Promise<FullTrendDetailResponse> {
    return this.get<FullTrendDetailResponse>(`/v1/api/trends/full/${encodeURIComponent(trendId)}`)
  }
}
