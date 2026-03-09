"""Tests for wireless convenience tools."""

import json

import httpx
import pytest
import respx

from mikrotik_management_mcp.models import RouterConnection
from mikrotik_management_mcp.tools.wireless import (
    ros_wireless_list,
    ros_wireless_registration_list,
    ros_wireless_scan,
    ros_wireless_security_profile_add,
)

BASE = "https://192.168.81.1:443/rest"


@pytest.fixture
def conn():
    return RouterConnection(host="192.168.81.1")


@pytest.mark.asyncio
class TestRosWirelessList:
    @respx.mock
    async def test_list_wireless_interfaces(self, conn):
        """GET /rest/interface/wireless returns wireless interfaces."""
        respx.get(f"{BASE}/interface/wireless").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {".id": "*1", "name": "wlan1", "mode": "ap-bridge", "ssid": "MikroTik"},
                ],
            )
        )
        result = await ros_wireless_list(connection=conn)
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == "wlan1"


@pytest.mark.asyncio
class TestRosWirelessScan:
    @respx.mock
    async def test_scan_posts_with_id_and_duration_as_string(self, conn):
        """POST /rest/interface/wireless/scan with .id and duration as string."""
        route = respx.post(f"{BASE}/interface/wireless/scan").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {"address": "AA:BB:CC:DD:EE:FF", "ssid": "TestNet", "signal-strength": "-60"},
                ],
            )
        )
        result = await ros_wireless_scan(connection=conn, interface="wlan1", duration=10)
        data = json.loads(result)
        assert isinstance(data, list)
        assert data[0]["ssid"] == "TestNet"
        # Verify POST body has .id and duration as string
        sent = json.loads(route.calls[0].request.content)
        assert sent[".id"] == "wlan1"
        assert sent["duration"] == "10"


@pytest.mark.asyncio
class TestRosWirelessSecurityProfileAdd:
    @respx.mock
    async def test_add_security_profile_with_hyphen_mapping(self, conn):
        """PUT /rest/interface/wireless/security-profiles with correct hyphen keys."""
        route = respx.put(f"{BASE}/interface/wireless/security-profiles").mock(
            return_value=httpx.Response(
                200,
                json={".id": "*2", "name": "my-profile", "mode": "dynamic-keys"},
            )
        )
        result = await ros_wireless_security_profile_add(
            connection=conn,
            name="my-profile",
            authentication_types="wpa2-psk",
            wpa2_pre_shared_key="supersecret",
        )
        data = json.loads(result)
        assert data["name"] == "my-profile"
        # Verify hyphenated keys in request body
        sent = json.loads(route.calls[0].request.content)
        assert sent["authentication-types"] == "wpa2-psk"
        assert sent["wpa2-pre-shared-key"] == "supersecret"
        assert sent["mode"] == "dynamic-keys"


@pytest.mark.asyncio
class TestRosWirelessRegistrationList:
    @respx.mock
    async def test_list_registration_table(self, conn):
        """GET /rest/interface/wireless/registration-table returns connected clients."""
        respx.get(f"{BASE}/interface/wireless/registration-table").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {".id": "*1", "interface": "wlan1", "mac-address": "AA:BB:CC:DD:EE:FF", "signal-strength": "-55"},
                    {".id": "*2", "interface": "wlan1", "mac-address": "11:22:33:44:55:66", "signal-strength": "-70"},
                ],
            )
        )
        result = await ros_wireless_registration_list(connection=conn)
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["mac-address"] == "AA:BB:CC:DD:EE:FF"
