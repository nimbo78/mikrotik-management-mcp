"""Pydantic models for MikroTik MCP server."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RouterConnection(BaseModel):
    """Connection parameters for a MikroTik device. Required in every tool call."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    host: str = Field(
        ..., description="IP address or hostname of the MikroTik router"
    )
    port: int = Field(
        default=443, description="REST API port (443 for HTTPS, 80 for HTTP)", ge=1, le=65535
    )
    username: str = Field(default="admin", description="RouterOS username")
    password: str = Field(default="", description="RouterOS password")
    ssl: bool = Field(default=True, description="Use HTTPS. Set False for HTTP.")
    verify_ssl: bool = Field(
        default=False, description="Verify SSL certificate. False for self-signed."
    )

    @field_validator("host")
    @classmethod
    def validate_host(cls, v: str) -> str:
        if not v:
            raise ValueError("Host cannot be empty")
        return v

    @property
    def base_url(self) -> str:
        scheme = "https" if self.ssl else "http"
        return f"{scheme}://{self.host}:{self.port}/rest"
