"""Tests for system tools: ros_system_info, ros_backup, ros_backup_download."""

import base64
import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from mikrotik_management_mcp.client import RouterOSError
from mikrotik_management_mcp.models import RouterConnection
from mikrotik_management_mcp.tools.system import (
    _format_bytes,
    ros_backup,
    ros_backup_download,
    ros_file_list,
    ros_system_info,
)

MOCK_SYSTEM_RESOURCE = {
    "uptime": "1d2h3m4s",
    "version": "7.16.2 (stable)",
    "board-name": "hAP ax3",
    "architecture-name": "arm",
    "cpu": "ARM",
    "cpu-count": "4",
    "cpu-load": "5",
    "total-memory": "1073741824",
    "free-memory": "536870912",
    "total-hdd-space": "134217728",
    "free-hdd-space": "67108864",
}


@pytest.fixture
def conn():
    return RouterConnection(host="192.168.81.1")


# ---------- _format_bytes ----------


class TestFormatBytes:
    def test_gigabytes(self):
        assert _format_bytes("1073741824") == "1.00 GB"

    def test_megabytes(self):
        assert _format_bytes("536870912") == "512.00 MB"

    def test_kilobytes(self):
        assert _format_bytes("2048") == "2.00 KB"

    def test_bytes(self):
        assert _format_bytes("512") == "512 B"

    def test_zero(self):
        assert _format_bytes("0") == "0 B"

    def test_invalid_string(self):
        assert _format_bytes("not-a-number") == "not-a-number"

    def test_empty_string(self):
        assert _format_bytes("") == ""

    def test_large_gb(self):
        # 2 GB
        assert _format_bytes("2147483648") == "2.00 GB"

    def test_exact_mb_boundary(self):
        assert _format_bytes("1048576") == "1.00 MB"

    def test_exact_kb_boundary(self):
        assert _format_bytes("1024") == "1.00 KB"


# ---------- ros_system_info ----------


@pytest.mark.asyncio
class TestRosSystemInfo:
    @respx.mock
    async def test_success(self, conn):
        respx.get("https://192.168.81.1:443/rest/system/resource").mock(
            return_value=httpx.Response(200, json=MOCK_SYSTEM_RESOURCE)
        )
        result = await ros_system_info(conn)

        assert "hAP ax3" in result
        assert "7.16.2 (stable)" in result
        assert "arm" in result
        assert "ARM" in result
        assert "4" in result  # cpu-count
        assert "5%" in result  # cpu-load
        assert "1.00 GB" in result  # total-memory
        assert "512.00 MB" in result  # free-memory
        assert "128.00 MB" in result  # total-hdd-space
        assert "64.00 MB" in result  # free-hdd-space
        assert "1d2h3m4s" in result

    @respx.mock
    async def test_success_list_response(self, conn):
        """RouterOS may return a list with a single dict."""
        respx.get("https://192.168.81.1:443/rest/system/resource").mock(
            return_value=httpx.Response(200, json=[MOCK_SYSTEM_RESOURCE])
        )
        result = await ros_system_info(conn)
        assert "hAP ax3" in result
        assert "7.16.2 (stable)" in result

    @respx.mock
    async def test_routeros_error(self, conn):
        respx.get("https://192.168.81.1:443/rest/system/resource").mock(
            return_value=httpx.Response(401, json={"message": "Unauthorized"})
        )
        result = await ros_system_info(conn)
        assert "RouterOS Error (401)" in result
        assert "Unauthorized" in result

    @respx.mock
    async def test_connection_error(self, conn):
        respx.get("https://192.168.81.1:443/rest/system/resource").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        result = await ros_system_info(conn)
        assert "Connection Error" in result
        assert "192.168.81.1" in result

    @respx.mock
    async def test_timeout_error(self, conn):
        respx.get("https://192.168.81.1:443/rest/system/resource").mock(
            side_effect=httpx.ReadTimeout("timed out")
        )
        result = await ros_system_info(conn)
        assert "Timeout" in result
        assert "192.168.81.1" in result

    @respx.mock
    async def test_unexpected_error(self, conn):
        respx.get("https://192.168.81.1:443/rest/system/resource").mock(
            side_effect=RuntimeError("something broke")
        )
        result = await ros_system_info(conn)
        assert "Unexpected Error" in result
        assert "RuntimeError" in result

    async def test_target_not_allowed(self):
        blocked_conn = RouterConnection(host="10.99.99.99")
        with patch(
            "mikrotik_management_mcp.tools.system.check_target_allowed",
            return_value=False,
        ):
            result = await ros_system_info(blocked_conn)
        assert "not in the allowed targets list" in result
        assert "10.99.99.99" in result


# ---------- ros_backup ----------


@pytest.mark.asyncio
class TestRosBackup:
    @respx.mock
    async def test_success(self, conn):
        respx.post("https://192.168.81.1:443/rest/system/backup/save").mock(
            return_value=httpx.Response(200, json={})
        )
        respx.get("https://192.168.81.1:443/rest/file").mock(
            return_value=httpx.Response(
                200,
                json=[{"name": "mybackup.backup", "size": "1048576"}],
            )
        )

        with patch("mikrotik_management_mcp.tools.system.asyncio.sleep", new_callable=AsyncMock):
            result = await ros_backup(conn, name="mybackup", backup_password="secret123")

        data = json.loads(result)
        assert data["success"] is True
        assert data["filename"] == "mybackup.backup"
        assert data["size"] == "1048576"

    @respx.mock
    async def test_backup_file_not_found(self, conn):
        """Backup command succeeds but file verification returns empty list."""
        respx.post("https://192.168.81.1:443/rest/system/backup/save").mock(
            return_value=httpx.Response(200, json={})
        )
        respx.get("https://192.168.81.1:443/rest/file").mock(
            return_value=httpx.Response(200, json=[])
        )

        with patch("mikrotik_management_mcp.tools.system.asyncio.sleep", new_callable=AsyncMock):
            result = await ros_backup(conn, name="missing", backup_password="secret")

        data = json.loads(result)
        assert data["success"] is True
        assert data["filename"] == "missing.backup"
        assert "note" in data

    @respx.mock
    async def test_routeros_error(self, conn):
        respx.post("https://192.168.81.1:443/rest/system/backup/save").mock(
            return_value=httpx.Response(400, json={"message": "failure"})
        )

        result = await ros_backup(conn, name="fail", backup_password="pw")
        assert "RouterOS Error (400)" in result
        assert "failure" in result

    @respx.mock
    async def test_connection_error(self, conn):
        respx.post("https://192.168.81.1:443/rest/system/backup/save").mock(
            side_effect=httpx.ConnectError("refused")
        )
        result = await ros_backup(conn, name="b", backup_password="p")
        assert "Connection Error" in result

    @respx.mock
    async def test_timeout_error(self, conn):
        respx.post("https://192.168.81.1:443/rest/system/backup/save").mock(
            side_effect=httpx.ReadTimeout("timed out")
        )
        result = await ros_backup(conn, name="b", backup_password="p")
        assert "Timeout" in result

    async def test_target_not_allowed(self):
        blocked_conn = RouterConnection(host="10.99.99.99")
        with patch(
            "mikrotik_management_mcp.tools.system.check_target_allowed",
            return_value=False,
        ):
            result = await ros_backup(blocked_conn, name="b", backup_password="p")
        assert "not in the allowed targets list" in result


# ---------- ros_backup_download ----------


@pytest.mark.asyncio
class TestRosBackupDownload:
    @respx.mock
    async def test_success(self, conn):
        file_content = b"\x00\x01\x02\x03binary-backup-data"
        respx.get("https://192.168.81.1:443/mybackup.backup").mock(
            return_value=httpx.Response(200, content=file_content)
        )

        result = await ros_backup_download(conn, filename="mybackup.backup")
        data = json.loads(result)

        assert data["filename"] == "mybackup.backup"
        assert data["size_bytes"] == len(file_content)
        assert base64.b64decode(data["content_base64"]) == file_content

    @respx.mock
    async def test_file_not_found(self, conn):
        respx.get("https://192.168.81.1:443/nofile.backup").mock(
            return_value=httpx.Response(404, text="Not Found")
        )

        result = await ros_backup_download(conn, filename="nofile.backup")
        assert "HTTP Error (404)" in result
        assert "nofile.backup" in result

    @respx.mock
    async def test_connection_error(self, conn):
        respx.get("https://192.168.81.1:443/test.backup").mock(
            side_effect=httpx.ConnectError("refused")
        )
        result = await ros_backup_download(conn, filename="test.backup")
        assert "Connection Error" in result

    @respx.mock
    async def test_timeout_error(self, conn):
        respx.get("https://192.168.81.1:443/test.backup").mock(
            side_effect=httpx.ReadTimeout("timed out")
        )
        result = await ros_backup_download(conn, filename="test.backup")
        assert "Timeout" in result

    async def test_target_not_allowed(self):
        blocked_conn = RouterConnection(host="10.99.99.99")
        with patch(
            "mikrotik_management_mcp.tools.system.check_target_allowed",
            return_value=False,
        ):
            result = await ros_backup_download(blocked_conn, filename="x.backup")
        assert "not in the allowed targets list" in result

    @respx.mock
    async def test_unexpected_error(self, conn):
        respx.get("https://192.168.81.1:443/test.backup").mock(
            side_effect=RuntimeError("something broke")
        )
        result = await ros_backup_download(conn, filename="test.backup")
        assert "Unexpected Error" in result
        assert "RuntimeError" in result


# ---------- ros_file_list ----------


@pytest.mark.asyncio
class TestRosFileList:
    @respx.mock
    async def test_success(self, conn):
        respx.get("https://192.168.81.1:443/rest/file").mock(
            return_value=httpx.Response(200, json=[
                {".id": "*1", "name": "backup.backup", "type": "backup", "size": "1048576"},
                {".id": "*2", "name": "export.rsc", "type": "script", "size": "2048"},
            ])
        )
        result = await ros_file_list(conn)
        data = json.loads(result)
        assert len(data) == 2
        assert data[0]["name"] == "backup.backup"
