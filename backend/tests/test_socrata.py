import httpx
import pytest

from app.ingestion.socrata import MAX_ATTEMPTS, SocrataClient, SocrataError

PORTAL = "https://portal.example"


def make_client(
    handler: httpx.MockTransport, sleeps: list[float], page_size: int = 2
) -> SocrataClient:
    return SocrataClient(
        httpx.Client(transport=handler),
        portal_url=PORTAL,
        page_size=page_size,
        delay=1.0,
        sleep=sleeps.append,
    )


def test_iter_rows_pages_until_a_short_page_and_waits_between_requests() -> None:
    requests: list[httpx.Request] = []
    rows = [{":id": f"row-{i}", "campo": i} for i in range(5)]

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        offset = int(request.url.params["$offset"])
        limit = int(request.url.params["$limit"])
        return httpx.Response(200, json=rows[offset : offset + limit])

    sleeps: list[float] = []
    client = make_client(httpx.MockTransport(handler), sleeps)

    assert list(client.iter_rows("abcd-1234")) == rows
    assert [r.url.params["$offset"] for r in requests] == ["0", "2", "4"]
    assert all(r.url.path == "/resource/abcd-1234.json" for r in requests)
    # Stable ordering and system fields are requested on every page.
    assert all(r.url.params["$order"] == ":id" for r in requests)
    assert all(r.url.params["$select"] == ":*, *" for r in requests)
    # One crawl-delay pause between pages.
    assert sleeps == [1.0, 1.0]


def test_server_errors_are_retried_with_backoff() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls < 3:
            return httpx.Response(503)
        return httpx.Response(200, json=[{":id": "row-1"}])

    sleeps: list[float] = []
    client = make_client(httpx.MockTransport(handler), sleeps)

    assert list(client.iter_rows("abcd-1234")) == [{":id": "row-1"}]
    assert calls == 3
    assert sleeps == [2.0, 4.0]


def test_gives_up_after_the_allowed_attempts() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ConnectError("sin conexión", request=request)

    client = make_client(httpx.MockTransport(handler), [])

    with pytest.raises(SocrataError, match="after 4 attempts"):
        list(client.iter_rows("abcd-1234"))
    assert calls == MAX_ATTEMPTS


def test_client_errors_fail_immediately() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(404, json={"message": "Not found"})

    client = make_client(httpx.MockTransport(handler), [])

    with pytest.raises(SocrataError, match="HTTP 404"):
        list(client.iter_rows("abcd-1234"))
    assert calls == 1


def test_a_response_that_is_not_a_list_is_an_error() -> None:
    client = make_client(
        httpx.MockTransport(lambda request: httpx.Response(200, json={"error": True})), []
    )
    with pytest.raises(SocrataError, match="not a list"):
        list(client.iter_rows("abcd-1234"))
