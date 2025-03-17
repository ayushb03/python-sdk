"""
Configuration settings for the MCP SDK.

This module provides configuration options that affect the behavior of the MCP SDK.
"""

from pydantic import BaseModel, Field

from mcp.shared.serialization_format import SerializationFormat


class MCPConfig(BaseModel):
    """
    MCP SDK configuration settings.
    
    Attributes:
        serialization_format: The default serialization format to use for all operations
    """
    
    serialization_format: SerializationFormat = Field(
        default=SerializationFormat.ORJSON,
        description="The default serialization format to use for all operations"
    )
    
    optimize_performance: bool = Field(
        default=True,
        description="Whether to enable performance optimizations like caching and pooling"
    )
    
    connection_timeout_seconds: float = Field(
        default=30.0,
        description="Default timeout for establishing connections"
    )
    
    request_timeout_seconds: float = Field(
        default=60.0,
        description="Default timeout for waiting for responses to requests"
    )


# Global configuration instance
# This can be modified by applications to change the default behavior
config = MCPConfig()


def configure(new_config: MCPConfig = None, **kwargs) -> None:
    """
    Configure the MCP SDK with new settings.
    
    Args:
        new_config: A complete MCPConfig instance to use for configuration
        **kwargs: Individual configuration settings to update
    """
    global config
    
    if new_config is not None:
        config = new_config
    else:
        # Update individual settings
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
            else:
                raise ValueError(f"Unknown configuration setting: {key}")


def get_serialization_format() -> SerializationFormat:
    """
    Get the currently configured serialization format.
    
    Returns:
        The current serialization format
    """
    return config.serialization_format 