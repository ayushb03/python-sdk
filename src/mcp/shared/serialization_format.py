"""
Serialization format options for MCP.

This module defines the available serialization formats and provides utilities
for working with them.
"""

from enum import Enum


class SerializationFormat(str, Enum):
    """
    Serialization format options for MCP.
    
    Attributes:
        JSON: Standard library JSON (human-readable, but slower)
        ORJSON: Optimized JSON implementation (human-readable, much faster)
        MSGPACK: MessagePack binary format (compact binary format)
        MSGSPEC: Schema-aware serialization (fastest with schemas)
        FLATBUFFERS: Google FlatBuffers (extremely fast binary format with zero-copy access)
    """
    
    JSON = "json"
    """Standard library JSON (human-readable, but slower)"""
    
    ORJSON = "orjson"  
    """Optimized JSON implementation (human-readable, much faster)"""
    
    MSGPACK = "msgpack"  
    """MessagePack binary format (compact binary format)"""
    
    MSGSPEC = "msgspec"  
    """Schema-aware serialization (fastest with schemas)"""
    
    FLATBUFFERS = "flatbuffers"
    """Google FlatBuffers (extremely fast binary format with zero-copy access)"""