import json

import pytest

from .conftest import skip_no_router, skip_not_destructive
from mikrotik_management_mcp.tools.command import ros_command
from mikrotik_management_mcp.tools.crud import ros_add, ros_get, ros_remove, ros_update
from mikrotik_management_mcp.tools.system import ros_backup


@skip_no_router
@skip_not_destructive
@pytest.mark.asyncio
class TestDestructive:
    async def test_crud_lifecycle(self, router_conn):
        """Create, read, update, and delete a firewall address-list entry."""
        # Add
        add_result = await ros_add(
            connection=router_conn,
            path="ip/firewall/address-list",
            data={
                "list": "mcp-test",
                "address": "198.51.100.1",
                "comment": "MCP integration test",
            },
        )
        add_data = json.loads(add_result)
        assert ".id" in add_data
        record_id = add_data[".id"]

        try:
            # Read
            get_result = await ros_get(
                connection=router_conn,
                path="ip/firewall/address-list",
                id=record_id,
            )
            get_data = json.loads(get_result)
            assert get_data["address"] == "198.51.100.1"

            # Update
            update_result = await ros_update(
                connection=router_conn,
                path="ip/firewall/address-list",
                id=record_id,
                data={"comment": "MCP test updated"},
            )
            update_data = json.loads(update_result)
            assert update_data["comment"] == "MCP test updated"
        finally:
            # Always clean up
            await ros_remove(
                connection=router_conn,
                path="ip/firewall/address-list",
                id=record_id,
            )

    async def test_command_ping(self, router_conn):
        result = await ros_command(
            connection=router_conn,
            path="tool/ping",
            data={"address": "127.0.0.1", "count": "1"},
        )
        # Should not be an error (may be empty list on some routers)
        assert "Connection Error" not in result

    async def test_backup_create(self, router_conn):
        result = await ros_backup(
            connection=router_conn,
            name="mcp-test-backup",
            backup_password="testpass123",
        )
        assert "mcp-test-backup" in result
        # Cleanup: remove backup file
        await ros_command(
            connection=router_conn,
            path="file/remove",
            data={".id": "mcp-test-backup.backup"},
        )
