"""Stateless REST API client for MikroTik RouterOS."""

import httpx

from .models import RouterConnection


class RouterOSError(Exception):
    """Error returned by RouterOS REST API."""

    def __init__(self, status_code: int, message: str, detail: str = ""):
        self.status_code = status_code
        self.message = message
        self.detail = detail
        super().__init__(f"RouterOS error {status_code}: {message}")


class RouterOSClient:
    """Stateless REST API client for RouterOS."""

    @staticmethod
    async def request(
        conn: RouterConnection,
        method: str,
        path: str,
        data: dict | None = None,
        params: dict | None = None,
        timeout: float = 30.0,
    ) -> dict | list | str:
        """Make a single REST API request to a RouterOS device."""
        url = f"{conn.base_url}/{path.strip('/')}"

        async with httpx.AsyncClient(
            verify=conn.verify_ssl,
            auth=(conn.username, conn.password),
            timeout=timeout,
        ) as client:
            response = await client.request(
                method=method,
                url=url,
                json=data,
                params=params,
            )

            if response.status_code >= 400:
                try:
                    error_body = response.json()
                except Exception:
                    error_body = response.text
                raise RouterOSError(
                    status_code=response.status_code,
                    message=(
                        error_body.get("message", str(error_body))
                        if isinstance(error_body, dict)
                        else str(error_body)
                    ),
                    detail=(
                        error_body.get("detail", "")
                        if isinstance(error_body, dict)
                        else ""
                    ),
                )

            if not response.content:
                return {"success": True}

            return response.json()

    @staticmethod
    async def download_file(
        conn: RouterConnection,
        filename: str,
        timeout: float = 120.0,
    ) -> bytes:
        """Download a file from RouterOS webserver (not REST API)."""
        scheme = "https" if conn.ssl else "http"
        url = f"{scheme}://{conn.host}:{conn.port}/{filename}"

        async with httpx.AsyncClient(
            verify=conn.verify_ssl,
            auth=(conn.username, conn.password),
            timeout=timeout,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
