"""`earlyforge` CLI — command-line access to the EarlyForge Trends API.

Wraps the same endpoints as the Python/JS/PHP SDKs and the MCP server:
the 4 free Pulse endpoints (top, by region, by category, trend detail)
plus the paid-plan full trends feed (list + detail). Contract:
docs/api/public-api-v1/openapi.yaml (repo root).
"""

from __future__ import annotations

import json
import os
import sys
from typing import Optional

import click

from .client import PulseApiError, PulseClient


def _resolve_api_key(api_key: Optional[str]) -> str:
    resolved = api_key or os.environ.get("EARLYFORGE_API_KEY")
    if not resolved:
        raise click.ClickException(
            "No API key provided. Pass --api-key or set EARLYFORGE_API_KEY. "
            "Generate one from Settings -> API Keys in the EarlyForge console "
            "(any account — Pulse access is free)."
        )
    return resolved


def _print_json(payload: object) -> None:
    click.echo(json.dumps(payload, indent=2, ensure_ascii=False))


@click.group()
def cli() -> None:
    """EarlyForge command-line client."""


@cli.group()
def pulse() -> None:
    """Query the free EarlyForge Pulse API (trend snapshots)."""


@pulse.command("top")
@click.option("--date", default=None, help="Past daily snapshot (YYYY-MM-DD). Omit for latest.")
@click.option("--locale", default=None, help='Locale for translated fields (e.g. "fr").')
@click.option("--api-key", default=None, help="API key. Defaults to $EARLYFORGE_API_KEY.")
@click.option("--base-url", default="https://api.earlyforge.ai", show_default=True)
def pulse_top(date: Optional[str], locale: Optional[str], api_key: Optional[str], base_url: str) -> None:
    """Global top trends — same snapshot as the Pulse homepage."""
    client = PulseClient(api_key=_resolve_api_key(api_key), base_url=base_url)
    _run(lambda: client.top_trends(date=date, locale=locale))


@pulse.command("region")
@click.argument("region")
@click.option("--date", default=None, help="Past daily snapshot (YYYY-MM-DD). Omit for latest.")
@click.option("--locale", default=None, help='Locale for translated fields (e.g. "fr").')
@click.option("--api-key", default=None, help="API key. Defaults to $EARLYFORGE_API_KEY.")
@click.option("--base-url", default="https://api.earlyforge.ai", show_default=True)
def pulse_region(
    region: str, date: Optional[str], locale: Optional[str], api_key: Optional[str], base_url: str
) -> None:
    """Top trends for a region (ISO 3166-1 alpha-2, e.g. US, FR)."""
    client = PulseClient(api_key=_resolve_api_key(api_key), base_url=base_url)
    _run(lambda: client.trends_by_region(region, date=date, locale=locale))


@pulse.command("category")
@click.argument("category")
@click.option("--date", default=None, help="Past daily snapshot (YYYY-MM-DD). Omit for latest.")
@click.option("--locale", default=None, help='Locale for translated fields (e.g. "fr").')
@click.option("--api-key", default=None, help="API key. Defaults to $EARLYFORGE_API_KEY.")
@click.option("--base-url", default="https://api.earlyforge.ai", show_default=True)
def pulse_category(
    category: str, date: Optional[str], locale: Optional[str], api_key: Optional[str], base_url: str
) -> None:
    """Top trends for a category (e.g. politics, tech)."""
    client = PulseClient(api_key=_resolve_api_key(api_key), base_url=base_url)
    _run(lambda: client.trends_by_category(category, date=date, locale=locale))


@pulse.command("trend")
@click.argument("trend_id")
@click.option("--api-key", default=None, help="API key. Defaults to $EARLYFORGE_API_KEY.")
@click.option("--base-url", default="https://api.earlyforge.ai", show_default=True)
def pulse_trend(trend_id: str, api_key: Optional[str], base_url: str) -> None:
    """Detail for one trend (score, description, sources, timeline)."""
    client = PulseClient(api_key=_resolve_api_key(api_key), base_url=base_url)
    _run(lambda: client.get_trend(trend_id))


@pulse.command("full")
@click.option("--region", default=None, help="Filter by region.")
@click.option("--category", default=None, help="Filter by category.")
@click.option("--page", default=1, show_default=True, type=int)
@click.option("--limit", default=20, show_default=True, type=int, help="Max 100.")
@click.option("--api-key", default=None, help="API key. Defaults to $EARLYFORGE_API_KEY.")
@click.option("--base-url", default="https://api.earlyforge.ai", show_default=True)
def pulse_full(
    region: Optional[str],
    category: Optional[str],
    page: int,
    limit: int,
    api_key: Optional[str],
    base_url: str,
) -> None:
    """Full trends feed (paid plans only — not "all trends unlocked").

    Every plan still reveals only a daily, random, category-diversified
    budget of trend names, same as the dashboard's Trends page. Items
    outside today's budget stay in the list with their name redacted
    ("name_locked": true). A free-plan key gets HTTP 402.
    """
    client = PulseClient(api_key=_resolve_api_key(api_key), base_url=base_url)
    _run(lambda: client.full_trends(region=region, category=category, page=page, limit=limit))


@pulse.command("full-trend")
@click.argument("trend_id")
@click.option("--api-key", default=None, help="API key. Defaults to $EARLYFORGE_API_KEY.")
@click.option("--base-url", default="https://api.earlyforge.ai", show_default=True)
def pulse_full_trend(trend_id: str, api_key: Optional[str], base_url: str) -> None:
    """Full detail for one trend (paid plans only).

    Returns HTTP 402 if the trend is outside today's visible-name
    budget — same restriction the dashboard's own detail panel enforces.
    """
    client = PulseClient(api_key=_resolve_api_key(api_key), base_url=base_url)
    _run(lambda: client.get_full_trend(trend_id))


def _run(call) -> None:
    try:
        _print_json(call())
    except PulseApiError as exc:
        click.echo(f"Error: {exc} ({exc.detail})" if exc.detail else f"Error: {exc}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
