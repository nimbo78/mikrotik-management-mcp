"""Tests for IPsec VPN convenience tools."""

import json

import httpx
import pytest
import respx

from mikrotik_management_mcp.models import RouterConnection
from mikrotik_management_mcp.tools.ipsec import (
    ros_ipsec_peer_list,
    ros_ipsec_identity_list,
    ros_ipsec_policy_list,
    ros_ipsec_installed_sa_list,
    ros_ipsec_peer_add,
)

BASE = "https://192.168.81.1:443/rest"


@pytest.fixture
def conn():
    return RouterConnection(host="192.168.81.1")


@pytest.mark.asyncio
class TestIpsecReadTools:
    @respx.mock
    async def test_peer_list(self, conn):
        respx.get(f"{BASE}/ip/ipsec/peer").mock(
            return_value=httpx.Response(200, json=[
                {".id": "*1", "address": "203.0.113.1", "exchange-mode": "ike2"},
            ])
        )
        result = await ros_ipsec_peer_list(conn)
        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["address"] == "203.0.113.1"

    @respx.mock
    async def test_identity_list(self, conn):
        respx.get(f"{BASE}/ip/ipsec/identity").mock(
            return_value=httpx.Response(200, json=[
                {".id": "*1", "peer": "peer1", "auth-method": "pre-shared-key"},
            ])
        )
        result = await ros_ipsec_identity_list(conn)
        data = json.loads(result)
        assert len(data) == 1

    @respx.mock
    async def test_policy_list(self, conn):
        respx.get(f"{BASE}/ip/ipsec/policy").mock(
            return_value=httpx.Response(200, json=[
                {".id": "*1", "src-address": "10.0.0.0/24", "dst-address": "10.1.0.0/24", "action": "encrypt"},
            ])
        )
        result = await ros_ipsec_policy_list(conn)
        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["action"] == "encrypt"

    @respx.mock
    async def test_installed_sa_list(self, conn):
        respx.get(f"{BASE}/ip/ipsec/installed-sa").mock(
            return_value=httpx.Response(200, json=[
                {".id": "*1", "src-address": "192.168.1.1", "dst-address": "203.0.113.1", "state": "mature"},
            ])
        )
        result = await ros_ipsec_installed_sa_list(conn)
        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["state"] == "mature"


@pytest.mark.asyncio
class TestIpsecPeerAdd:
    @respx.mock
    async def test_add_full_params(self, conn):
        route = respx.put(f"{BASE}/ip/ipsec/peer").mock(
            return_value=httpx.Response(201, json={".id": "*2", "address": "203.0.113.2"})
        )
        result = await ros_ipsec_peer_add(
            conn, address="203.0.113.2", exchange_mode="ike2",
            profile="ipsec-profile1", comment="site-to-site"
        )
        data = json.loads(result)
        assert data["address"] == "203.0.113.2"
        body = json.loads(route.calls[0].request.content)
        assert body["address"] == "203.0.113.2"
        assert body["exchange-mode"] == "ike2"
        assert body["profile"] == "ipsec-profile1"
        assert body["comment"] == "site-to-site"

    @respx.mock
    async def test_add_minimal(self, conn):
        route = respx.put(f"{BASE}/ip/ipsec/peer").mock(
            return_value=httpx.Response(201, json={".id": "*3"})
        )
        await ros_ipsec_peer_add(conn, address="203.0.113.3")
        body = json.loads(route.calls[0].request.content)
        assert body["address"] == "203.0.113.3"
        assert body["exchange-mode"] == "main"
        assert "profile" not in body

    @respx.mock
    async def test_add_disabled(self, conn):
        route = respx.put(f"{BASE}/ip/ipsec/peer").mock(
            return_value=httpx.Response(201, json={".id": "*4"})
        )
        await ros_ipsec_peer_add(conn, address="203.0.113.4", disabled=True)
        body = json.loads(route.calls[0].request.content)
        assert body["disabled"] == "true"
