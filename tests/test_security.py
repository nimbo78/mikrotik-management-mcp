import os
import pytest
from mikrotik_management_mcp.security import (
    check_client_allowed,
    check_target_allowed,
    load_security_config,
)


class TestCheckTargetAllowed:
    def test_no_restrictions(self):
        assert check_target_allowed("192.168.81.1") is True

    def test_ip_in_allowed_cidr(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_TARGETS", "192.168.81.0/24")
        load_security_config()
        assert check_target_allowed("192.168.81.1") is True
        assert check_target_allowed("10.0.0.1") is False

    def test_multiple_cidrs(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_TARGETS", "192.168.81.0/24,10.0.0.0/8")
        load_security_config()
        assert check_target_allowed("10.0.0.1") is True
        assert check_target_allowed("172.16.0.1") is False

    def test_hostname_allowed_by_default(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_TARGETS", "192.168.81.0/24")
        load_security_config()
        assert check_target_allowed("my-router.local") is True

    def teardown_method(self):
        os.environ.pop("ALLOWED_TARGETS", None)
        os.environ.pop("ALLOWED_CLIENTS", None)
        os.environ.pop("MCP_AUTH_TOKEN", None)
        load_security_config()


class TestCheckClientAllowed:
    def test_no_restrictions(self):
        assert check_client_allowed("1.2.3.4") is True

    def test_client_in_allowed(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_CLIENTS", "192.168.81.0/24")
        load_security_config()
        assert check_client_allowed("192.168.81.100") is True
        assert check_client_allowed("10.0.0.1") is False

    def test_invalid_client_ip_denied(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_CLIENTS", "192.168.81.0/24")
        load_security_config()
        assert check_client_allowed("not-an-ip") is False

    def teardown_method(self):
        os.environ.pop("ALLOWED_TARGETS", None)
        os.environ.pop("ALLOWED_CLIENTS", None)
        os.environ.pop("MCP_AUTH_TOKEN", None)
        load_security_config()


class TestLoadSecurityConfig:
    def test_loads_token(self, monkeypatch):
        monkeypatch.setenv("MCP_AUTH_TOKEN", "abc123")
        load_security_config()
        from mikrotik_management_mcp.security import MCP_AUTH_TOKEN
        assert MCP_AUTH_TOKEN == "abc123"

    def test_empty_token_is_none(self, monkeypatch):
        monkeypatch.delenv("MCP_AUTH_TOKEN", raising=False)
        load_security_config()
        from mikrotik_management_mcp.security import MCP_AUTH_TOKEN
        assert MCP_AUTH_TOKEN is None

    def teardown_method(self):
        os.environ.pop("ALLOWED_TARGETS", None)
        os.environ.pop("ALLOWED_CLIENTS", None)
        os.environ.pop("MCP_AUTH_TOKEN", None)
        load_security_config()
