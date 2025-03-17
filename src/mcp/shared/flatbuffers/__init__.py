"""
FlatBuffers implementation for MCP.

This module contains the implementation of FlatBuffers serialization for MCP messages.
"""

# Re-export flatbuffers implementation
from .serializer import (
    serialize_message,
    deserialize_message,
    flatbuffers_available
)