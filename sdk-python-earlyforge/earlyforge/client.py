"""Client for the EarlyForge Trends API.

Covers 2 tiers under the same /v1/api/trends/* prefix:

  - Pulse mirror (free, any plan):
      GET /v1/api/trends/top
      GET /v1/api/trends/region/{region}
      GET /v1/api/trends/category/{category}
      GET /v1/api/trends/{trend_id}
  - Full trends feed (paid plans only — NOT "all trends unlocked", see
    full_trends()):
      GET /v1/api/trends/full
      GET /v1/api/trends/full/{trend_id}

Contract: docs/api/public-api-v1/openapi.yaml (repo root). This client
never sends a parameter the OpenAPI spec doesn't document.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from urllib.parse import quote

import httpx

DEFAULT_BASE_URL = "https://api.earlyforge.ai"
DEFAULT_TIMEOUT_SECONDS = 15.0


class PulseApiError(Exception):
    """Raised when the Pulse API returns a non-2xx response.

    Attributes:
        status_code: The HTTP status code, when available.
        detail: The error detail returned by the API, when available.
    """

    def __init__(self, message: str, *, status_code: Optional[int] = None, detail: Optional[str] = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


class PulseClient:
    """A thin, synchronous HTTP client for the EarlyForge Pulse API.

    Example:
        >>> client = PulseClient(api_key="ef_live_xxxxxxxxxxxxxxxx")
        >>> snapshot = client.top_trends(locale="fr")
        >>> snapshot["trends"][0]["display_name"]
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        *,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        clean_params = {k: v for k, v in (params or {}).items() if v is not None}
        url = f"{self.base_url}{path}"
        try:
            response = httpx.get(
                url,
                params=clean_params,
                headers=self._headers(),
                timeout=self.timeout,
            )
        except httpx.RequestError as exc:
            raise PulseApiError(f"Could not reach EarlyForge API at {url}: {exc}") from exc

        if response.status_code >= 400:
            detail = None
            try:
                detail = response.json().get("detail")
            except Exception:
                detail = response.text[:300] or None
            raise PulseApiError(
                f"EarlyForge API returned HTTP {response.status_code} for {url}",
                status_code=response.status_code,
                detail=detail,
            )

        return response.json()

    def top_trends(self, *, date: Optional[str] = None, locale: Optional[str] = None) -> Any:
        """Global top trends — same daily snapshot as the Pulse homepage.

        Args:
            date: Pick a past daily snapshot (YYYY-MM-DD). Omit for the latest.
            locale: Locale for translated fields (e.g. "fr").

        Returns:
            {"trends": [...], "total": int, "cached_at": str, "cache_ttl_seconds": int}
        """
        return self._get("/v1/api/trends/top", {"date": date, "locale": locale})

    def trends_by_region(
        self, region: str, *, date: Optional[str] = None, locale: Optional[str] = None
    ) -> Any:
        """Top trends for a region — same snapshot as the Pulse region view.

        Args:
            region: ISO 3166-1 alpha-2 region code (e.g. "US", "FR").
            date: Pick a past daily snapshot (YYYY-MM-DD). Omit for the latest.
            locale: Locale for translated fields (e.g. "fr").
        """
        return self._get(f"/v1/api/trends/region/{quote(region, safe='')}", {"date": date, "locale": locale})

    def trends_by_category(
        self, category: str, *, date: Optional[str] = None, locale: Optional[str] = None
    ) -> Any:
        """Top trends for a category — same snapshot as the Pulse category view.

        Args:
            category: Category filter (e.g. "politics", "tech").
            date: Pick a past daily snapshot (YYYY-MM-DD). Omit for the latest.
            locale: Locale for translated fields (e.g. "fr").
        """
        return self._get(f"/v1/api/trends/category/{quote(category, safe='')}", {"date": date, "locale": locale})

    def get_trend(self, trend_id: str) -> Any:
        """Trend detail — same payload as the public trend detail page.

        Args:
            trend_id: The trend's id, e.g. "tr_a1b2c3" (from top_trends()).
        """
        return self._get(f"/v1/api/trends/{quote(trend_id, safe='')}")

    def full_trends(
        self,
        *,
        region: Optional[str] = None,
        category: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Any:
        """Full trends feed — paid plans only, and NOT "all trends unlocked".

        Every plan still reveals only a daily, random, category-diversified
        budget of trend names (same budget the dashboard's Trends page shows
        for this org today). Items outside that budget stay in the list but
        with their name fields redacted (``name_locked: true``). A free-plan
        key gets ``PulseApiError`` with ``status_code=402`` before this even
        runs.

        Args:
            region: Filter by region.
            category: Filter by category.
            page: Page number, default 1.
            limit: Items per page, default 20, max 100.

        Returns:
            {"items": [...], "total": int, "page": int, "per_page": int}
        """
        return self._get(
            "/v1/api/trends/full",
            {"region": region, "category": category, "page": page, "limit": limit},
        )

    def get_full_trend(self, trend_id: str) -> Any:
        """Full detail for one trend — paid plans only.

        Returns ``PulseApiError`` with ``status_code=402`` if the trend is
        outside today's visible-name budget — same restriction the
        dashboard's own detail panel enforces.

        Args:
            trend_id: The trend's id, e.g. "tr_a1b2c3" (from full_trends()).
        """
        return self._get(f"/v1/api/trends/full/{quote(trend_id, safe='')}")
