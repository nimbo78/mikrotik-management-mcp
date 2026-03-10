"""Tests for simple queue convenience tools."""

import json

import httpx
import pytest
import respx

from mikrotik_management_mcp.models import RouterConnection
from mikrotik_management_mcp.tools.queues import (
    ros_queue_simple_add,
    ros_queue_simple_list,
    ros_queue_simple_update,
    ros_queue_simple_remove,
    ros_queue_simple_enable,
    ros_queue_simple_disable,
)

BASE = "https://192.168.81.1:443/rest"


@pytest.fixture
def conn():
    return RouterConnection(host="192.168.81.1")


@pytest.mark.asyncio
class TestQueueSimpleTools:
    @respx.mock
    async def test_add_full_params(self, conn):
        route = respx.put(f"{BASE}/queue/simple").mock(
            return_value=httpx.Response(201, json={".id": "*1", "name": "q1"})
        )
        result = await ros_queue_simple_add(
            conn, name="q1", target="10.0.0.100/32",
            max_limit="10M/10M", burst_limit="20M/20M",
            burst_threshold="8M/8M", burst_time="10/10", comment="test"
        )
        data = json.loads(result)
        assert data[".id"] == "*1"
        body = json.loads(route.calls[0].request.content)
        assert body["name"] == "q1"
        assert body["target"] == "10.0.0.100/32"
        assert body["max-limit"] == "10M/10M"
        assert body["burst-limit"] == "20M/20M"
        assert body["burst-threshold"] == "8M/8M"
        assert body["burst-time"] == "10/10"

    @respx.mock
    async def test_add_minimal(self, conn):
        route = respx.put(f"{BASE}/queue/simple").mock(
            return_value=httpx.Response(201, json={".id": "*2", "name": "q2"})
        )
        await ros_queue_simple_add(conn, name="q2", target="10.0.0.0/24")
        body = json.loads(route.calls[0].request.content)
        assert body["name"] == "q2"
        assert body["target"] == "10.0.0.0/24"
        assert "max-limit" not in body

    @respx.mock
    async def test_add_disabled(self, conn):
        route = respx.put(f"{BASE}/queue/simple").mock(
            return_value=httpx.Response(201, json={".id": "*3"})
        )
        await ros_queue_simple_add(conn, name="q3", target="10.0.0.0/24", disabled=True)
        body = json.loads(route.calls[0].request.content)
        assert body["disabled"] == "true"

    @respx.mock
    async def test_list(self, conn):
        respx.get(f"{BASE}/queue/simple").mock(
            return_value=httpx.Response(200, json=[
                {".id": "*1", "name": "q1", "target": "10.0.0.100/32", "max-limit": "10M/10M"},
            ])
        )
        result = await ros_queue_simple_list(conn)
        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["max-limit"] == "10M/10M"

    @respx.mock
    async def test_update(self, conn):
        route = respx.patch(f"{BASE}/queue/simple/*1").mock(
            return_value=httpx.Response(200, json={".id": "*1", "max-limit": "20M/20M"})
        )
        result = await ros_queue_simple_update(conn, id="*1", max_limit="20M/20M")
        data = json.loads(result)
        assert data["max-limit"] == "20M/20M"
        body = json.loads(route.calls[0].request.content)
        assert body["max-limit"] == "20M/20M"

    @respx.mock
    async def test_remove(self, conn):
        respx.delete(f"{BASE}/queue/simple/*1").mock(
            return_value=httpx.Response(200, content=b"")
        )
        result = await ros_queue_simple_remove(conn, id="*1")
        data = json.loads(result)
        assert data["success"] is True

    @respx.mock
    async def test_enable(self, conn):
        route = respx.patch(f"{BASE}/queue/simple/*1").mock(
            return_value=httpx.Response(200, json={".id": "*1", "disabled": "false"})
        )
        result = await ros_queue_simple_enable(conn, id="*1")
        body = json.loads(route.calls[0].request.content)
        assert body["disabled"] == "false"

    @respx.mock
    async def test_disable(self, conn):
        route = respx.patch(f"{BASE}/queue/simple/*1").mock(
            return_value=httpx.Response(200, json={".id": "*1", "disabled": "true"})
        )
        result = await ros_queue_simple_disable(conn, id="*1")
        body = json.loads(route.calls[0].request.content)
        assert body["disabled"] == "true"
