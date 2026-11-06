from __future__ import annotations

import httpx
import pytest
from click.testing import CliRunner

from earlyforge_cli.main import cli


def _handler(request: httpx.Request) -> httpx.Response:
    assert request.headers["authorization"] == "Bearer ef_live_test"
    if request.url.path == "/v1/api/trends/top":
        return httpx.Response(200, json={"trends": [], "total": 0})
    if request.url.path == "/v1/api/trends/full":
        return httpx.Response(
            200, json={"items": [{"trend_id": "tr_1"}], "total": 1, "page": 1, "per_page": 20}
        )
    return httpx.Response(404, json={"detail": "Not found"})


@pytest.fixture(autouse=True)
def _patch_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = httpx.MockTransport(_handler)

    def fake_get(url, *, params=None, headers=None, timeout=None):
        with httpx.Client(transport=transport) as client:
            return client.get(url, params=params, headers=headers, timeout=timeout)

    monkeypatch.setattr(httpx, "get", fake_get)


def test_pulse_top_prints_json() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["pulse", "top", "--api-key", "ef_live_test"])
    assert result.exit_code == 0
    assert '"trends": []' in result.output


def test_pulse_full_prints_json() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["pulse", "full", "--api-key", "ef_live_test"])
    assert result.exit_code == 0
    assert '"total": 1' in result.output


def test_missing_api_key_errors_cleanly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EARLYFORGE_API_KEY", raising=False)
    runner = CliRunner()
    result = runner.invoke(cli, ["pulse", "top"])
    assert result.exit_code != 0
    assert "No API key provided" in result.output
