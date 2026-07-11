from typing import Any

import pytest
from starlette.requests import Request

from app.api.v1.moods import _extract_ip
from app.core.config import settings


def make_request(xff: str | None, client_host: str = "10.0.0.1") -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if xff is not None:
        headers.append((b"x-forwarded-for", xff.encode()))
    scope: dict[str, Any] = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/moods",
        "headers": headers,
        "client": (client_host, 12345),
        "query_string": b"",
    }
    return Request(scope)


def test_no_trusted_proxies_ignores_header(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "trusted_proxy_count", 0)
    request = make_request("6.6.6.6", client_host="10.0.0.1")
    assert _extract_ip(request) == "10.0.0.1"


def test_no_header_falls_back_to_peer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "trusted_proxy_count", 1)
    request = make_request(None, client_host="10.0.0.1")
    assert _extract_ip(request) == "10.0.0.1"


def test_one_proxy_takes_rightmost_hop(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "trusted_proxy_count", 1)
    request = make_request("6.6.6.6, 4.4.4.4")
    assert _extract_ip(request) == "4.4.4.4"


def test_spoofed_prefix_is_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "trusted_proxy_count", 1)
    request = make_request("1.1.1.1, 2.2.2.2, 4.4.4.4")
    assert _extract_ip(request) == "4.4.4.4"


def test_two_proxies_takes_second_from_right(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "trusted_proxy_count", 2)
    request = make_request("6.6.6.6, 9.9.9.9, 10.1.1.1")
    assert _extract_ip(request) == "9.9.9.9"


def test_chain_shorter_than_proxy_count(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "trusted_proxy_count", 2)
    request = make_request("9.9.9.9")
    assert _extract_ip(request) == "9.9.9.9"


def test_whitespace_only_header_falls_back_to_peer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "trusted_proxy_count", 1)
    request = make_request("  ,  ", client_host="10.0.0.1")
    assert _extract_ip(request) == "10.0.0.1"
