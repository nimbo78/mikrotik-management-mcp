"""Tests for DNS convenience tools."""

import json

import httpx
import pytest
import respx

from mikrotik_management_mcp.models import RouterConnection
from mikrotik_management_mcp.tools.dns import (
    ros_dns_cache_flush,
    ros_dns_get,
    ros_dns_set_servers,
    ros_dns_static_add,
)

BASE = "https://192.168.81.1:443/rest"


@pytest.fixture
def conn():
    return RouterConnection(host="192.168.81.1")


@pytest.mark.asyncio
class TestRosDnsGet:
    @respx.mock
    async def test_get_config(self, conn):
        respx.get(f"{BASE}/ip/dns").mock(
            return_value=httpx.Response(
                200,
                json={
                    "servers": "8.8.8.8,8.8.4.4",
                    "allow-remote-requests": "false",
                    "cache-size": "2048",
                },
            )
        )
        result = await ros_dns_get(conn)
        data = json.loads(result)
        assert data["servers"] == "8.8.8.8,8.8.4.4"
        assert data["allow-remote-requests"] == "false"


@pytest.mark.asyncio
class TestRosDnsSetServers:
    @respx.mock
    async def test_set_servers_with_allow_remote(self, conn):
        route = respx.post(f"{BASE}/ip/dns/set").mock(
            return_value=httpx.Response(200, json={})
        )
        result = await ros_dns_set_servers(
            conn, servers="1.1.1.1,8.8.8.8", allow_remote_requests=True
        )
        # Verify POST method and body content
        request = route.calls[0].request
        assert request.method == "POST"
        body = json.loads(request.content)
        assert body["servers"] == "1.1.1.1,8.8.8.8"
        assert body["allow-remote-requests"] == "true"


@pytest.mark.asyncio
class TestRosDnsStaticAdd:
    @respx.mock
    async def test_a_record(self, conn):
        route = respx.put(f"{BASE}/ip/dns/static").mock(
            return_value=httpx.Response(
                201,
                json={
                    ".id": "*1",
                    "name": "myhost.local",
                    "address": "192.168.1.50",
                },
            )
        )
        result = await ros_dns_static_add(
            conn, name="myhost.local", address="192.168.1.50"
        )
        data = json.loads(result)
        assert data[".id"] == "*1"
        assert data["name"] == "myhost.local"
        body = json.loads(route.calls[0].request.content)
        assert body["name"] == "myhost.local"
        assert body["address"] == "192.168.1.50"

    @respx.mock
    async def test_cname_record(self, conn):
        route = respx.put(f"{BASE}/ip/dns/static").mock(
            return_value=httpx.Response(201, json={".id": "*2", "name": "www.example.com", "type": "CNAME", "cname": "example.com"})
        )
        result = await ros_dns_static_add(conn, name="www.example.com", type="CNAME", cname="example.com")
        data = json.loads(result)
        assert data["type"] == "CNAME"
        body = json.loads(route.calls[0].request.content)
        assert body["name"] == "www.example.com"
        assert body["type"] == "CNAME"
        assert body["cname"] == "example.com"
        assert "address" not in body

    @respx.mock
    async def test_fwd_record(self, conn):
        route = respx.put(f"{BASE}/ip/dns/static").mock(
            return_value=httpx.Response(201, json={".id": "*3", "name": "internal.corp", "type": "FWD", "forward-to": "10.0.0.53"})
        )
        result = await ros_dns_static_add(conn, name="internal.corp", type="FWD", forward_to="10.0.0.53", match_subdomain=True)
        body = json.loads(route.calls[0].request.content)
        assert body["type"] == "FWD"
        assert body["forward-to"] == "10.0.0.53"
        assert body["match-subdomain"] == "true"

    @respx.mock
    async def test_nxdomain_record(self, conn):
        route = respx.put(f"{BASE}/ip/dns/static").mock(
            return_value=httpx.Response(201, json={".id": "*4", "type": "NXDOMAIN"})
        )
        await ros_dns_static_add(conn, name="blocked.example.com", type="NXDOMAIN")
        body = json.loads(route.calls[0].request.content)
        assert body["type"] == "NXDOMAIN"
        assert body["name"] == "blocked.example.com"

    @respx.mock
    async def test_mx_record(self, conn):
        route = respx.put(f"{BASE}/ip/dns/static").mock(
            return_value=httpx.Response(201, json={".id": "*5"})
        )
        await ros_dns_static_add(conn, name="example.com", type="MX", mx_exchange="mail.example.com", mx_preference="10")
        body = json.loads(route.calls[0].request.content)
        assert body["type"] == "MX"
        assert body["mx-exchange"] == "mail.example.com"
        assert body["mx-preference"] == "10"

    @respx.mock
    async def test_srv_record(self, conn):
        route = respx.put(f"{BASE}/ip/dns/static").mock(
            return_value=httpx.Response(201, json={".id": "*6"})
        )
        await ros_dns_static_add(
            conn, name="_sip._tcp.example.com", type="SRV",
            srv_target="sip.example.com", srv_port="5060", srv_priority="10", srv_weight="100",
        )
        body = json.loads(route.calls[0].request.content)
        assert body["type"] == "SRV"
        assert body["srv-target"] == "sip.example.com"
        assert body["srv-port"] == "5060"
        assert body["srv-priority"] == "10"
        assert body["srv-weight"] == "100"

    @respx.mock
    async def test_txt_record(self, conn):
        route = respx.put(f"{BASE}/ip/dns/static").mock(
            return_value=httpx.Response(201, json={".id": "*7"})
        )
        await ros_dns_static_add(conn, name="example.com", type="TXT", text="v=spf1 include:example.com ~all")
        body = json.loads(route.calls[0].request.content)
        assert body["type"] == "TXT"
        assert body["text"] == "v=spf1 include:example.com ~all"

    @respx.mock
    async def test_ns_record(self, conn):
        route = respx.put(f"{BASE}/ip/dns/static").mock(
            return_value=httpx.Response(201, json={".id": "*8"})
        )
        await ros_dns_static_add(conn, name="example.com", type="NS", ns="ns1.example.com")
        body = json.loads(route.calls[0].request.content)
        assert body["type"] == "NS"
        assert body["ns"] == "ns1.example.com"

    @respx.mock
    async def test_regexp_pattern(self, conn):
        route = respx.put(f"{BASE}/ip/dns/static").mock(
            return_value=httpx.Response(201, json={".id": "*9"})
        )
        await ros_dns_static_add(conn, regexp=".*\\.ads\\..*", type="NXDOMAIN")
        body = json.loads(route.calls[0].request.content)
        assert body["regexp"] == ".*\\.ads\\..*"
        assert body["type"] == "NXDOMAIN"
        assert "name" not in body

    @respx.mock
    async def test_address_list(self, conn):
        route = respx.put(f"{BASE}/ip/dns/static").mock(
            return_value=httpx.Response(201, json={".id": "*A"})
        )
        await ros_dns_static_add(conn, name="example.com", address="1.2.3.4", address_list="allowed-sites")
        body = json.loads(route.calls[0].request.content)
        assert body["address-list"] == "allowed-sites"
        assert body["address"] == "1.2.3.4"

    async def test_no_name_or_regexp_returns_error(self, conn):
        result = await ros_dns_static_add(conn, address="1.2.3.4")
        assert "Error" in result
        assert "name" in result.lower() or "regexp" in result.lower()

    @respx.mock
    async def test_disabled_and_ttl(self, conn):
        route = respx.put(f"{BASE}/ip/dns/static").mock(
            return_value=httpx.Response(201, json={".id": "*B"})
        )
        await ros_dns_static_add(conn, name="test.local", address="10.0.0.1", ttl="1d", disabled=True, comment="temp")
        body = json.loads(route.calls[0].request.content)
        assert body["ttl"] == "1d"
        assert body["disabled"] == "true"
        assert body["comment"] == "temp"


@pytest.mark.asyncio
class TestRosDnsCacheFlush:
    @respx.mock
    async def test_cache_flush(self, conn):
        route = respx.post(f"{BASE}/ip/dns/cache/flush").mock(
            return_value=httpx.Response(200, json={})
        )
        result = await ros_dns_cache_flush(conn)
        # Verify POST to correct path
        assert route.calls[0].request.method == "POST"
        assert route.calls[0].request.url.path == "/rest/ip/dns/cache/flush"
