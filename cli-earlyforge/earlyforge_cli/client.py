"""Minimal, standalone Trends API client used by the CLI.

Deliberately self-contained (duplicates the method shape of
tools/sdk-python-earlyforge/earlyforge/client.py) so this package has no
dependency on another, as-yet-unpublished package. Contract:
docs/api/public-api-v1/openapi.yaml (repo root).
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from urllib.parse import quote

import httpx

DEFAULT_BASE_URL = "https://api.earlyforge.ai"
DEFAULT_TIMEOUT_SECONDS = 15.0


class PulseApiError(Exception):
    def __init__(self, message: str, *, status_code: Optional[int] = None, detail: Optional[str] = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


class PulseClient:
    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        clean_params = {k: v for k, v in (params or {}).items() if v is not None}
        url = f"{self.base_url}{path}"
        try:
            response = httpx.get(
                url,
                params=clean_params,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
        except httpx.RequestError as exc:
            raise PulseApiError(f"Could not reach EarlyForge API at {url}: {exc}") from exc

        if response.status_code >= 400:
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
        return self._get("/v1/api/trends/top", {"date": date, "locale": locale})

    def trends_by_region(self, region: str, *, date: Optional[str] = None, locale: Optional[str] = None) -> Any:
        return self._get(f"/v1/api/trends/region/{quote(region, safe='')}", {"date": date, "locale": locale})

    def trends_by_category(self, category: str, *, date: Optional[str] = None, locale: Optional[str] = None) -> Any:
        return self._get(f"/v1/api/trends/category/{quote(category, safe='')}", {"date": date, "locale": locale})

    def get_trend(self, trend_id: str) -> Any:
        return self._get(f"/v1/api/trends/{quote(trend_id, safe='')}")

    def full_trends(
        self,
        *,
        region: Optional[str] = None,
        category: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Any:
        return self._get(
            "/v1/api/trends/full",
            {"region": region, "category": category, "page": page, "limit": limit},
        )

    def get_full_trend(self, trend_id: str) -> Any:
        return self._get(f"/v1/api/trends/full/{quote(trend_id, safe='')}")
