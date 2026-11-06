"""MCP server wrapping the EarlyForge Public API — Trends v1.

Exposes tools over MCP so an AI agent can query EarlyForge's trend
data directly, across both tiers of the /v1/api/trends/* prefix:

  Pulse mirror (free, any plan):
    - top_trends:          GET /v1/api/trends/top
    - trends_by_region:    GET /v1/api/trends/region/{region}
    - trends_by_category:  GET /v1/api/trends/category/{category}
    - get_trend:           GET /v1/api/trends/{trend_id}

  Full trends feed (paid plans only — NOT "all trends unlocked", see
  full_trends() below):
    - full_trends:         GET /v1/api/trends/full
    - get_full_trend:      GET /v1/api/trends/full/{trend_id}

The Pulse tools are a verbatim authenticated mirror of the free,
anonymous Pulse data already shown on pulse.earlyforge.ai — same daily
snapshot, same trend count, same fields. There is no limit/page/sort
parameter here that doesn't already exist on the public page: a
free-plan key never sees more than an anonymous visitor already can.

Also exposes the EarlyForge documentation (docs.earlyforge.ai) via
`list_docs` / `read_docs` — these read the site's public `llms.txt` /
`llms-full.txt` routes, no account or API key required at all. Only
the trends tools above need EARLYFORGE_API_KEY.

Contract: docs/api/public-api-v1/openapi.yaml (repo root).

Auth: the trends tools read EARLYFORGE_API_KEY from the environment
and send it as `Authorization: Bearer {key}`. Get a key from Settings
-> API Keys in the EarlyForge console — any account works, Pulse
access is free; full_trends/get_full_trend additionally need a paid
plan on the organization that key belongs to. The doc tools need no
auth at all.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx
from mcp.server.fastmcp import FastMCP

API_BASE = os.environ.get("EARLYFORGE_API_BASE", "https://api.earlyforge.ai")
API_KEY = os.environ.get("EARLYFORGE_API_KEY")
DOCS_BASE = os.environ.get("EARLYFORGE_DOCS_BASE", "https://docs.earlyforge.ai")

mcp = FastMCP("earlyforge-trends")


def _headers() -> Dict[str, str]:
    if not API_KEY:
        raise RuntimeError(
            "EARLYFORGE_API_KEY is not set. Generate a key from "
            "Settings -> API Keys in the EarlyForge console (any "
            "account — Pulse access is free) and set it in this "
            "server's environment."
        )
    return {"Authorization": f"Bearer {API_KEY}"}


async def _get(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    params = {k: v for k, v in (params or {}).items() if v is not None}
    url = f"{API_BASE}{path}"
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
            response = await client.get(url, params=params, headers=_headers())
    except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError) as exc:
        raise RuntimeError(f"Could not reach EarlyForge API at {url}: {exc}") from exc

    if response.status_code == 401:
        # This surface has no monthly quota (it's free, cached Pulse
        # data) — a 401 here is always a missing/invalid/revoked/
        # disabled key, never a quota error.
        raise RuntimeError(
            "EarlyForge API key is missing, invalid, revoked, or disabled."
        )
    if response.status_code == 402:
        try:
            detail = response.json().get("detail", {})
        except Exception:
            detail = {}
        code = detail.get("code") if isinstance(detail, dict) else None
        if code == "trend_locked":
            raise RuntimeError(
                "This trend is outside today's visible-name budget for this "
                "plan — locked on the dashboard too, not an API-specific "
                "restriction."
            )
        raise RuntimeError(
            "The full trends feed requires a paid plan. This organization "
            "is on the free plan, which only reaches the Pulse mirror "
            "(top_trends/trends_by_region/trends_by_category/get_trend)."
        )
    if response.status_code == 404:
        raise RuntimeError("Trend not found.")
    if response.status_code == 502:
        raise RuntimeError("EarlyForge's Pulse service is temporarily unavailable.")
    if response.status_code != 200:
        raise RuntimeError(
            f"EarlyForge API returned HTTP {response.status_code}: {response.text[:300]}"
        )

    return response.json()


@mcp.tool()
async def top_trends(date: Optional[str] = None, locale: Optional[str] = None) -> Any:
    """Global top trends — the same daily snapshot shown on the Pulse homepage.

    Args:
        date: Pick a past daily snapshot (YYYY-MM-DD). Omit for the latest.
        locale: Locale for translated fields (e.g. "fr").

    Returns:
        {"trends": [...], "total", "cached_at", "cache_ttl_seconds"} —
        same shape and count as pulse.earlyforge.ai, nothing more.
    """
    return await _get("/v1/api/trends/top", {"date": date, "locale": locale})


@mcp.tool()
async def trends_by_region(
    region: str, date: Optional[str] = None, locale: Optional[str] = None
) -> Any:
    """Top trends for a region — same snapshot as the Pulse region view.

    Args:
        region: ISO 3166-1 alpha-2 region code (e.g. "US", "FR").
        date: Pick a past daily snapshot (YYYY-MM-DD). Omit for the latest.
        locale: Locale for translated fields (e.g. "fr").
    """
    return await _get(f"/v1/api/trends/region/{region}", {"date": date, "locale": locale})


@mcp.tool()
async def trends_by_category(
    category: str, date: Optional[str] = None, locale: Optional[str] = None
) -> Any:
    """Top trends for a category — same snapshot as the Pulse category view.

    Args:
        category: Category filter (e.g. "politics", "tech").
        date: Pick a past daily snapshot (YYYY-MM-DD). Omit for the latest.
        locale: Locale for translated fields (e.g. "fr").
    """
    return await _get(
        f"/v1/api/trends/category/{category}", {"date": date, "locale": locale}
    )


@mcp.tool()
async def get_trend(trend_id: str) -> Any:
    """Get detail for one trend — same payload as the public trend detail page.

    Args:
        trend_id: The trend's id, e.g. "tr_a1b2c3" (from top_trends).

    Returns:
        Trend detail with score, description, sources, and `timeline`.
    """
    return await _get(f"/v1/api/trends/{trend_id}")


@mcp.tool()
async def full_trends(
    region: Optional[str] = None,
    category: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
) -> Any:
    """Full trends feed — paid plans only, and NOT "all trends unlocked".

    Every plan still reveals only a daily, random, category-diversified
    budget of trend names — exactly the same trends this organization's
    dashboard Trends page shows unlocked today, no more, no less. A
    trend outside today's budget stays in the list but with its name
    redacted (name_locked: true). Calling this with a free-plan key
    raises an error before any of that even runs.

    Args:
        region: Filter by region.
        category: Filter by category.
        page: Page number, default 1.
        limit: Items per page, default 20, max 100.

    Returns:
        {"items": [...], "total", "page", "per_page"} — locked items
        keep their place in the list with name fields redacted.
    """
    return await _get(
        "/v1/api/trends/full",
        {"region": region, "category": category, "page": page, "limit": limit},
    )


@mcp.tool()
async def get_full_trend(trend_id: str) -> Any:
    """Full detail for one trend — paid plans only.

    Raises an error if the trend is outside today's visible-name
    budget — same restriction the dashboard's own detail panel
    enforces, not an API-specific one.

    Args:
        trend_id: The trend's id, e.g. "tr_a1b2c3" (from full_trends()).

    Returns:
        Full trend detail: score, status, editorial fields, timeline.
    """
    return await _get(f"/v1/api/trends/full/{trend_id}")


async def _get_text(url: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
            response = await client.get(url)
    except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError) as exc:
        raise RuntimeError(f"Could not reach {url}: {exc}") from exc
    if response.status_code != 200:
        raise RuntimeError(f"{url} returned HTTP {response.status_code}")
    return response.text


@mcp.tool()
async def list_docs() -> str:
    """List every EarlyForge documentation page (title + URL + short description).

    No account or API key required — this reads the public
    docs.earlyforge.ai/llms.txt index. Use read_docs() to fetch the
    full content of every page in one call, or follow a URL from this
    index yourself.
    """
    return await _get_text(f"{DOCS_BASE}/llms.txt")


@mcp.tool()
async def read_docs() -> str:
    """Read the complete EarlyForge documentation, concatenated.

    No account or API key required — this reads the public
    docs.earlyforge.ai/llms-full.txt route (every guide, including the
    Pulse API reference, SDKs, CLI, and MCP setup, in one plain-text
    response). Prefer list_docs() first if you only need to find one
    page's URL rather than the whole corpus.
    """
    return await _get_text(f"{DOCS_BASE}/llms-full.txt")


@mcp.prompt()
def editorial_watch(country: Optional[str] = None, sector: Optional[str] = None) -> str:
    """Build an editorial trend-watch briefing for a country and/or sector.

    Guides the agent to use top_trends / trends_by_region / trends_by_category
    / get_trend to compile a briefing, and tells it how to frame the
    free-vs-paid distinction honestly if the user asks for more than this
    data covers.
    """
    scope_bits = []
    if country:
        scope_bits.append(f"country {country}")
    if sector:
        scope_bits.append(f"sector {sector}")
    scope = " and ".join(scope_bits) if scope_bits else "the global trend landscape"

    return f"""You are compiling an editorial trend-watch briefing for {scope} using the
EarlyForge Trends tools (top_trends, trends_by_region, trends_by_category, get_trend).

Steps:
1. Call the tool matching the requested scope ({"trends_by_region" if country else "trends_by_category" if sector else "top_trends"}
   with the appropriate argument), then get_trend on the 3-5 most relevant results for
   fuller context (score, description, sources, timeline).
2. Summarize the briefing: what's trending, why it matters, how fresh it is
   (detected_at / hours_since_detection), and cite sources.

Be honest about what this data is and isn't:
- top_trends/trends_by_region/trends_by_category/get_trend are EarlyForge's
  free Pulse tier: today's daily snapshot, the same one shown on
  pulse.earlyforge.ai — roughly the top trends for the requested scope,
  refreshed once a day. Available on every plan, no paid plan required.
- full_trends/get_full_trend need a paid-plan API key and give a bigger,
  paginated slice of the trend corpus (region/category filters, page/limit) —
  but NOT "all trends unlocked": every plan, including paid ones, still only
  reveals a daily, random, category-diversified budget of trend names (same
  budget the dashboard's Trends page shows). A trend outside that budget
  comes back name-redacted (list) or locked (detail) — not a bug, not an
  API-specific restriction.
- If the user asks for something neither tier can do — true real-time
  monitoring instead of a daily snapshot, or seeing every trend name
  regardless of the daily budget — say so plainly and point to
  earlyforge.ai/pricing for current plan limits. Don't oversell it or invent
  features or numbers that aren't in the tool output.
"""


if __name__ == "__main__":
    mcp.run()
