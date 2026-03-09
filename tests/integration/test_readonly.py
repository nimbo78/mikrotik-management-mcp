import json

import pytest

from .conftest import skip_no_router
from mikrotik_management_mcp.tools.crud import ros_get
from mikrotik_management_mcp.tools.system import ros_system_info


@skip_no_router
@pytest.mark.asyncio
class TestReadOnly:
    async def test_system_info(self, router_conn):
        result = await ros_system_info(connection=router_conn)
        assert "Version" in result or "version" in result
        assert "Error" not in result

    async def test_get_interfaces(self, router_conn):
        result = await ros_get(connection=router_conn, path="interface")
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) > 0

    async def test_get_system_resource(self, router_conn):
        result = await ros_get(connection=router_conn, path="system/resource")
        data = json.loads(result)
        assert isinstance(data, (list, dict))

    async def test_get_with_proplist(self, router_conn):
        result = await ros_get(
            connection=router_conn, path="interface", proplist="name,type"
        )
        data = json.loads(result)
        assert isinstance(data, list)
