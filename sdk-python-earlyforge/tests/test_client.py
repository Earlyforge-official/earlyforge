from __future__ import annotations

import httpx
import pytest

from earlyforge import PulseApiError, PulseClient


def _handler(request: httpx.Request) -> httpx.Response:
    assert request.headers["authorization"] == "Bearer ef_live_test"
    if request.url.path == "/v1/api/trends/top":
        return httpx.Response(200, json={"trends": [], "total": 0})
    if request.url.path == "/v1/api/trends/region/US":
        return httpx.Response(200, json={"trends": [{"trend_id": "tr_1"}], "total": 1})
    if request.url.path == "/v1/api/trends/tr_missing":
        return httpx.Response(404, json={"detail": "Not found"})
    if request.url.path == "/v1/api/trends/full":
        if request.url.params.get("region") == "locked-org":
            return httpx.Response(
                402,
                json={"detail": {"error": "upgrade_required", "upgrade_url": "/settings/billing"}},
            )
        return httpx.Response(
            200,
            json={"items": [{"trend_id": "tr_1"}], "total": 1, "page": 1, "per_page": 20},
        )
    if request.url.path == "/v1/api/trends/full/tr_locked":
        return httpx.Response(
            402, json={"detail": {"error": "This trend is locked on your plan", "code": "trend_locked"}}
        )
    return httpx.Response(500, json={"detail": "unexpected"})


@pytest.fixture(autouse=True)
def _patch_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = httpx.MockTransport(_handler)

    def fake_get(url, *, params=None, headers=None, timeout=None):
        with httpx.Client(transport=transport) as client:
            return client.get(url, params=params, headers=headers, timeout=timeout)

    monkeypatch.setattr(httpx, "get", fake_get)


def test_top_trends_sends_bearer_token_and_builds_url() -> None:
    client = PulseClient(api_key="ef_live_test", base_url="https://api.test")
    result = client.top_trends(locale="fr")
    assert result == {"trends": [], "total": 0}


def test_trends_by_region_builds_path_param() -> None:
    client = PulseClient(api_key="ef_live_test", base_url="https://api.test")
    result = client.trends_by_region("US")
    assert result["total"] == 1


def test_get_trend_raises_pulse_api_error_on_404() -> None:
    client = PulseClient(api_key="ef_live_test", base_url="https://api.test")
    with pytest.raises(PulseApiError) as excinfo:
        client.get_trend("tr_missing")
    assert excinfo.value.status_code == 404


def test_requires_api_key() -> None:
    with pytest.raises(ValueError):
        PulseClient(api_key="")


def test_full_trends_returns_items_with_total() -> None:
    client = PulseClient(api_key="ef_live_test", base_url="https://api.test")
    result = client.full_trends(limit=20)
    assert result["total"] == 1
    assert result["items"][0]["trend_id"] == "tr_1"


def test_full_trends_raises_402_on_free_plan() -> None:
    client = PulseClient(api_key="ef_live_test", base_url="https://api.test")
    with pytest.raises(PulseApiError) as excinfo:
        client.full_trends(region="locked-org")
    assert excinfo.value.status_code == 402
    assert excinfo.value.detail["error"] == "upgrade_required"


def test_get_full_trend_raises_402_trend_locked() -> None:
    client = PulseClient(api_key="ef_live_test", base_url="https://api.test")
    with pytest.raises(PulseApiError) as excinfo:
        client.get_full_trend("tr_locked")
    assert excinfo.value.status_code == 402
    assert excinfo.value.detail["code"] == "trend_locked"
