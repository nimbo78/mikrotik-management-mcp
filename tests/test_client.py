import pytest
import httpx
import respx
from mikrotik_management_mcp.client import RouterOSClient, RouterOSError
from mikrotik_management_mcp.models import RouterConnection


@pytest.fixture
def conn():
    return RouterConnection(host="192.168.81.1")


@pytest.mark.asyncio
class TestRouterOSClient:
    @respx.mock
    async def test_get_success(self, conn):
        respx.get("https://192.168.81.1:443/rest/ip/address").mock(
            return_value=httpx.Response(200, json=[{"address": "10.0.0.1/24", ".id": "*1"}])
        )
        result = await RouterOSClient.request(conn, "GET", "ip/address")
        assert isinstance(result, list)
        assert result[0]["address"] == "10.0.0.1/24"

    @respx.mock
    async def test_put_success(self, conn):
        respx.put("https://192.168.81.1:443/rest/ip/address").mock(
            return_value=httpx.Response(201, json={".id": "*2", "address": "10.0.0.2/24"})
        )
        result = await RouterOSClient.request(
            conn, "PUT", "ip/address", data={"address": "10.0.0.2/24", "interface": "ether1"}
        )
        assert result[".id"] == "*2"

    @respx.mock
    async def test_delete_empty_response(self, conn):
        respx.delete("https://192.168.81.1:443/rest/ip/address/*1").mock(
            return_value=httpx.Response(204, content=b"")
        )
        result = await RouterOSClient.request(conn, "DELETE", "ip/address/*1")
        assert result == {"success": True}

    @respx.mock
    async def test_error_400(self, conn):
        respx.get("https://192.168.81.1:443/rest/bad/path").mock(
            return_value=httpx.Response(
                400, json={"detail": "no such command", "message": "bad request"}
            )
        )
        with pytest.raises(RouterOSError) as exc_info:
            await RouterOSClient.request(conn, "GET", "bad/path")
        assert exc_info.value.status_code == 400
        assert "bad request" in exc_info.value.message

    @respx.mock
    async def test_error_401(self, conn):
        respx.get("https://192.168.81.1:443/rest/system/resource").mock(
            return_value=httpx.Response(401, text="Unauthorized")
        )
        with pytest.raises(RouterOSError) as exc_info:
            await RouterOSClient.request(conn, "GET", "system/resource")
        assert exc_info.value.status_code == 401

    @respx.mock
    async def test_get_with_query_params(self, conn):
        respx.get("https://192.168.81.1:443/rest/ip/address").mock(
            return_value=httpx.Response(200, json=[])
        )
        result = await RouterOSClient.request(
            conn, "GET", "ip/address", params={"network": "10.0.0.0"}
        )
        assert result == []

    @respx.mock
    async def test_http_connection(self):
        http_conn = RouterConnection(host="192.168.81.1", port=80, ssl=False)
        respx.get("http://192.168.81.1:80/rest/interface").mock(
            return_value=httpx.Response(200, json=[])
        )
        result = await RouterOSClient.request(http_conn, "GET", "interface")
        assert result == []

    @respx.mock
    async def test_path_slash_stripping(self, conn):
        respx.get("https://192.168.81.1:443/rest/ip/address").mock(
            return_value=httpx.Response(200, json=[])
        )
        result = await RouterOSClient.request(conn, "GET", "/ip/address/")
        assert result == []


@pytest.mark.asyncio
class TestDownloadFile:
    @respx.mock
    async def test_download_success(self):
        conn = RouterConnection(host="192.168.81.1")
        respx.get("https://192.168.81.1:443/test.backup").mock(
            return_value=httpx.Response(200, content=b"\x00\x01\x02\x03")
        )
        result = await RouterOSClient.download_file(conn, "test.backup")
        assert result == b"\x00\x01\x02\x03"

    @respx.mock
    async def test_download_http(self):
        http_conn = RouterConnection(host="192.168.81.1", port=80, ssl=False)
        respx.get("http://192.168.81.1:80/backup.backup").mock(
            return_value=httpx.Response(200, content=b"data")
        )
        result = await RouterOSClient.download_file(http_conn, "backup.backup")
        assert result == b"data"
