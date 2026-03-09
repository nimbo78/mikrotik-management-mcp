import pytest
from mikrotik_management_mcp.models import RouterConnection


class TestRouterConnection:
    def test_minimal_connection(self):
        conn = RouterConnection(host="192.168.81.1")
        assert conn.host == "192.168.81.1"
        assert conn.port == 443
        assert conn.username == "admin"
        assert conn.password == ""
        assert conn.ssl is True
        assert conn.verify_ssl is False

    def test_base_url_https(self):
        conn = RouterConnection(host="192.168.81.1")
        assert conn.base_url == "https://192.168.81.1:443/rest"

    def test_base_url_http(self):
        conn = RouterConnection(host="192.168.81.1", port=80, ssl=False)
        assert conn.base_url == "http://192.168.81.1:80/rest"

    def test_empty_host_raises(self):
        with pytest.raises(ValueError):
            RouterConnection(host="")

    def test_host_whitespace_stripped(self):
        conn = RouterConnection(host="  192.168.81.1  ")
        assert conn.host == "192.168.81.1"

    def test_invalid_port_raises(self):
        with pytest.raises(ValueError):
            RouterConnection(host="192.168.81.1", port=0)

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValueError):
            RouterConnection(host="192.168.81.1", bogus="nope")

    def test_custom_credentials(self):
        conn = RouterConnection(
            host="10.0.0.1", port=8443, username="api", password="secret123"
        )
        assert conn.username == "api"
        assert conn.password == "secret123"
        assert conn.port == 8443
