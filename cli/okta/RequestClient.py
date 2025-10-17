from requests import get, post, put, patch, delete
from typing import Callable, Any
import logging

logger = logging.getLogger(__name__)

# Default timeout for HTTP requests (in seconds)
DEFAULT_TIMEOUT = 30


class HttpRequestClient:
    """
    HTTP client for making requests to the Okta API.

    Handles pagination, error handling, and response parsing.
    """

    def __init__(
        self, base_headers: dict, base_url: str, timeout: int = DEFAULT_TIMEOUT
    ) -> None:
        self.base_headers = base_headers
        self.base_url = base_url.rstrip("/")  # Remove trailing slash if present
        self.timeout = timeout

    def get(
        self,
        path: str = "",
        params: dict | None = None,
        headers: dict | None = None,
        cb: Callable | None = None,
    ) -> list:
        """
        Makes a GET request with automatic pagination support.

        Args:
            path: API endpoint path
            params: Query parameters
            headers: Additional headers to merge with base headers
            cb: Optional callback function called with accumulated results

        Returns:
            list: Accumulated results from all pages
        """
        params = params or {}
        headers = headers or {}
        _headers = self.base_headers | headers
        _url = f"{self.base_url}/{path.lstrip('/')}"
        results = []

        while _url:
            logger.debug(f"GET {_url}")
            r = get(_url, params=params, headers=_headers, timeout=self.timeout)
            r.raise_for_status()
            current_results = r.json()

            # Handle both single objects and arrays
            if isinstance(current_results, list):
                results.extend(current_results)
            else:
                results.append(current_results)

            if cb:
                cb(results)

            # Get next page URL from Link header
            next_link = r.links.get("next", {}).get("url")
            _url = next_link

        return results

    def post(
        self,
        path: str = "",
        params: dict | None = None,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        """
        Makes a POST request.

        Args:
            path: API endpoint path
            params: Query parameters
            data: Request body data
            headers: Additional headers to merge with base headers

        Returns:
            Response JSON data
        """
        params = params or {}
        data = data or {}
        headers = headers or {}
        _headers = self.base_headers | {"Content-Type": "application/json"} | headers
        _url = f"{self.base_url}/{path.lstrip('/')}"

        logger.debug(f"POST {_url}")
        logger.info(_url)
        r = post(_url, json=data, params=params, headers=_headers, timeout=self.timeout)
        r.raise_for_status()

        return r.json()

    def patch(
        self,
        path: str = "",
        data: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        """
        Makes a PATCH request.

        Args:
            path: API endpoint path
            data: Request body data
            params: Query parameters
            headers: Additional headers to merge with base headers

        Returns:
            Response JSON data
        """
        params = params or {}
        data = data or {}
        headers = headers or {}
        _headers = self.base_headers | {"Content-Type": "application/json"} | headers
        _url = f"{self.base_url}/{path.lstrip('/')}"

        logger.debug(f"PATCH {_url}")
        r = patch(
            _url, json=data, params=params, headers=_headers, timeout=self.timeout
        )
        r.raise_for_status()

        return r.json()

    def put(
        self,
        path: str = "",
        data: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        """
        Makes a PUT request.

        Args:
            path: API endpoint path
            data: Request body data
            params: Query parameters
            headers: Additional headers to merge with base headers

        Returns:
            Response JSON data
        """
        params = params or {}
        data = data or {}
        headers = headers or {}
        _headers = self.base_headers | {"Content-Type": "application/json"} | headers
        _url = f"{self.base_url}/{path.lstrip('/')}"

        logger.debug(f"PUT {_url}")
        r = put(_url, json=data, params=params, headers=_headers, timeout=self.timeout)
        r.raise_for_status()

        return r.json()

    def delete(
        self,
        path: str = "",
        data: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> None:
        """
        Makes a DELETE request.

        Args:
            path: API endpoint path
            data: Request body data (optional)
            params: Query parameters
            headers: Additional headers to merge with base headers

        Returns:
            None (DELETE typically returns 204 No Content)
        """
        params = params or {}
        data = data or {}
        headers = headers or {}
        _headers = self.base_headers | headers
        _url = f"{self.base_url}/{path.lstrip('/')}"

        logger.debug(f"DELETE {_url}")
        r = delete(
            _url,
            json=data if data else None,
            params=params,
            headers=_headers,
            timeout=self.timeout,
        )
        r.raise_for_status()

        # DELETE typically returns 204 No Content
        if r.status_code >= 200 and r.status_code < 400:
            return None

        return r.json() if r.text else None
