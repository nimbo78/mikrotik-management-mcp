import os

import pytest

from mikrotik_management_mcp.models import RouterConnection

ROUTER_HOST = os.environ.get("TEST_ROUTER_HOST")
ROUTER_PORT = int(os.environ.get("TEST_ROUTER_PORT", "443"))
ROUTER_USER = os.environ.get("TEST_ROUTER_USER", "admin")
ROUTER_PASSWORD = os.environ.get("TEST_ROUTER_PASSWORD", "")
ROUTER_SSL = os.environ.get("TEST_ROUTER_SSL", "true").lower() == "true"
ROUTER_DESTRUCTIVE = os.environ.get("TEST_ROUTER_DESTRUCTIVE", "false").lower() == "true"

skip_no_router = pytest.mark.skipif(
    not ROUTER_HOST, reason="TEST_ROUTER_HOST not set"
)
skip_not_destructive = pytest.mark.skipif(
    not ROUTER_DESTRUCTIVE, reason="TEST_ROUTER_DESTRUCTIVE not set to true"
)


@pytest.fixture
def router_conn():
    if not ROUTER_HOST:
        pytest.skip("TEST_ROUTER_HOST not set")
    return RouterConnection(
        host=ROUTER_HOST,
        port=ROUTER_PORT,
        username=ROUTER_USER,
        password=ROUTER_PASSWORD,
        ssl=ROUTER_SSL,
    )
