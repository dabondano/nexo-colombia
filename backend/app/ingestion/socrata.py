"""Client for datasets published on a Socrata open-data portal (datos.gov.co).

Uses the public SODA API. Requests are paginated, ordered by the stable system
row id, and spaced out to respect the portal's crawl delay.
"""

import time
from collections.abc import Callable, Iterator, Sequence
from typing import Any

import httpx

PORTAL_URL = "https://www.datos.gov.co"
USER_AGENT = "NEXO-Colombia/0.1 (public-interest research platform)"
# The portal's robots.txt asks for one second between requests.
CRAWL_DELAY_SECONDS = 1.0
PAGE_SIZE = 1000
MAX_ATTEMPTS = 4

Row = dict[str, Any]


class SocrataError(RuntimeError):
    """The portal could not be read after the allowed number of attempts."""


class SocrataClient:
    def __init__(
        self,
        client: httpx.Client | None = None,
        *,
        portal_url: str = PORTAL_URL,
        page_size: int = PAGE_SIZE,
        delay: float = CRAWL_DELAY_SECONDS,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._client = client or httpx.Client(
            headers={"User-Agent": USER_AGENT}, timeout=httpx.Timeout(90.0)
        )
        self._portal_url = portal_url.rstrip("/")
        self._page_size = page_size
        self._delay = delay
        self._sleep = sleep

    def dataset_url(self, dataset_id: str) -> str:
        return f"{self._portal_url}/d/{dataset_id}"

    def iter_rows(
        self, dataset_id: str, *, where: str | None = None, fields: Sequence[str] | None = None
    ) -> Iterator[Row]:
        """Yield the rows of a dataset, including Socrata system fields (':id', ...).

        `where` filters at the portal (SoQL); `fields` names the only columns
        requested, so columns NEXO must not hold are never downloaded.
        """
        offset = 0
        while True:
            page = self._get_page(dataset_id, offset, where=where, fields=fields)
            yield from page
            if len(page) < self._page_size:
                return
            offset += self._page_size
            self._sleep(self._delay)

    def _get_page(
        self,
        dataset_id: str,
        offset: int,
        *,
        where: str | None = None,
        fields: Sequence[str] | None = None,
    ) -> list[Row]:
        url = f"{self._portal_url}/resource/{dataset_id}.json"
        params = {
            "$select": ":id, :updated_at, " + ", ".join(fields) if fields else ":*, *",
            "$order": ":id",
            "$limit": str(self._page_size),
            "$offset": str(offset),
        }
        if where:
            params["$where"] = where
        last_error: Exception | None = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = self._client.get(url, params=params)
                if response.status_code >= 500 or response.status_code == 429:
                    raise httpx.HTTPStatusError(
                        f"HTTP {response.status_code}", request=response.request, response=response
                    )
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, list):
                    raise SocrataError(f"Unexpected response for {dataset_id}: not a list")
                return data
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code < 500 and exc.response.status_code != 429:
                    raise SocrataError(
                        f"{dataset_id}: HTTP {exc.response.status_code} at offset {offset}"
                    ) from exc
                last_error = exc
            except httpx.TransportError as exc:
                last_error = exc
            if attempt < MAX_ATTEMPTS:
                self._sleep(self._delay * 2**attempt)
        raise SocrataError(
            f"{dataset_id}: failed at offset {offset} after {MAX_ATTEMPTS} attempts"
        ) from last_error
