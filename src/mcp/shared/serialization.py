"""
High-performance serialization utilities for MCP.

This module provides optimized serialization/deserialization functions that can be used as drop-in
replacements for the standard JSON functions, with significantly better performance.
"""

import json
from typing import Any, Callable, Optional, Type, TypeVar

import orjson
import msgpack
import msgspec
from pydantic import BaseModel

from mcp.shared.config import get_serialization_format
from mcp.shared.serialization_format import SerializationFormat

# Type variables for generic functions
T = TypeVar("T")

# Conditionally import FlatBuffers
try:
    from mcp.shared.flatbuffers import serialize_message, deserialize_message, flatbuffers_available
    _FLATBUFFERS_AVAILABLE = flatbuffers_available()
except ImportError:
    _FLATBUFFERS_AVAILABLE = False


def configure_serialization(format: SerializationFormat) -> None:
    """Configure the default serialization format."""
    global DEFAULT_FORMAT
    DEFAULT_FORMAT = format


def dumps(obj: Any, format: Optional[SerializationFormat] = None) -> bytes:
    """
    Serialize an object to bytes using the specified format.
    
    Args:
        obj: The object to serialize
        format: The serialization format to use (defaults to the configured global format)
        
    Returns:
        The serialized data as bytes
    """
    format = format or get_serialization_format()
    
    if format == SerializationFormat.JSON:
        return json.dumps(obj).encode("utf-8")
    elif format == SerializationFormat.ORJSON:
        # Handle JSONRPCMessage specifically for better performance
        if hasattr(obj, 'model_dump'):
            # For Pydantic models, convert to dict first
            obj_dict = obj.model_dump(by_alias=True, mode="json", exclude_none=True)
            return orjson.dumps(obj_dict)
        return orjson.dumps(obj)
    elif format == SerializationFormat.MSGPACK:
        # Handle JSONRPCMessage specifically for better performance
        if hasattr(obj, 'model_dump'):
            # For Pydantic models, convert to dict first
            obj_dict = obj.model_dump(by_alias=True, mode="json", exclude_none=True)
            return msgpack.packb(obj_dict, use_bin_type=True)
        return msgpack.packb(obj, use_bin_type=True)
    elif format == SerializationFormat.MSGSPEC:
        # Handle JSONRPCMessage specifically for better performance
        if hasattr(obj, 'model_dump'):
            # For Pydantic models, convert to dict first
            obj_dict = obj.model_dump(by_alias=True, mode="json", exclude_none=True)
            return msgspec.json.encode(obj_dict)
        return msgspec.json.encode(obj)
    elif format == SerializationFormat.FLATBUFFERS:
        if not _FLATBUFFERS_AVAILABLE:
            raise ImportError("FlatBuffers is not available. Install with 'pip install flatbuffers'")
        
        # For JSONRPCMessage, use our specialized serializer
        if hasattr(obj, 'root') and hasattr(obj, 'model_dump'):
            try:
                from mcp.shared.flatbuffers import serialize_message
                return serialize_message(obj)
            except Exception as e:
                # If specialized serialization fails, fall back to JSON
                obj_dict = obj.model_dump(by_alias=True, mode="json", exclude_none=True)
                return orjson.dumps(obj_dict)
        
        # Fallback to JSON serialization for non-JSONRPCMessage objects
        # This is a temporary solution until we implement FlatBuffers for all types
        if hasattr(obj, 'model_dump'):
            obj_dict = obj.model_dump(by_alias=True, mode="json", exclude_none=True)
            return orjson.dumps(obj_dict)
        return orjson.dumps(obj)
    else:
        raise ValueError(f"Unsupported serialization format: {format}")


def loads(data: bytes, format: Optional[SerializationFormat] = None, type_: Optional[Type[T]] = None) -> Any:
    """
    Deserialize bytes to an object using the specified format.
    
    Args:
        data: The data to deserialize
        format: The serialization format to use (defaults to the configured global format)
        type_: Optional type to deserialize into (for msgspec schema validation)
        
    Returns:
        The deserialized object
    """
    format = format or get_serialization_format()
    
    if format == SerializationFormat.JSON:
        return json.loads(data.decode("utf-8"))
    elif format == SerializationFormat.ORJSON:
        return orjson.loads(data)
    elif format == SerializationFormat.MSGPACK:
        return msgpack.unpackb(data, raw=False)
    elif format == SerializationFormat.MSGSPEC:
        if type_ is not None:
            return msgspec.json.decode(data, type=type_)
        return msgspec.json.decode(data)
    elif format == SerializationFormat.FLATBUFFERS:
        if not _FLATBUFFERS_AVAILABLE:
            raise ImportError("FlatBuffers is not available. Install with 'pip install flatbuffers'")
        
        try:
            # First check if this is a JSONRPCMessage type
            if len(data) > 4 and data[0:4] == b'FLAT':
                # This appears to be a FlatBuffers message
                from mcp.shared.flatbuffers import deserialize_message
                return deserialize_message(data)
            
            # If it doesn't have the FlatBuffers header, fall back to JSON
            if type_ is not None and hasattr(type_, 'model_validate'):
                # If we have a Pydantic model type, use it
                json_data = orjson.loads(data)
                return type_.model_validate(json_data)
            
            # Otherwise just return the raw JSON data
            return orjson.loads(data)
        except Exception as e:
            # If deserialization fails, try a simpler approach
            return orjson.loads(data)
    else:
        raise ValueError(f"Unsupported serialization format: {format}")


def model_dumps(model: BaseModel, format: Optional[SerializationFormat] = None) -> bytes:
    """
    Serialize a Pydantic model to bytes using the specified format.
    
    This is optimized for Pydantic models, handling all the necessary conversions.
    
    Args:
        model: The Pydantic model to serialize
        format: The serialization format to use (defaults to global configuration)
        
    Returns:
        The serialized data as bytes
    """
    # Pydantic models have a model_dump method for converting to dict
    model_dict = model.model_dump(by_alias=True, mode="json", exclude_none=True)
    return dumps(model_dict, format=format)


def model_loads(data: bytes, model_type: Type[T], format: Optional[SerializationFormat] = None) -> T:
    """
    Deserialize bytes to a Pydantic model using the specified format.
    
    Args:
        data: The data to deserialize
        model_type: The Pydantic model type to deserialize into
        format: The serialization format to use (defaults to global configuration)
        
    Returns:
        The deserialized Pydantic model
    """
    # First deserialize to a dict
    dict_data = loads(data, format=format)
    # Then convert to the Pydantic model
    return model_type.model_validate(dict_data)


# Cache of struct types for msgspec optimized serialization
_STRUCT_CACHE = {}


def get_msgspec_struct(model_type: Type[BaseModel]) -> Type:
    """
    Convert a Pydantic model type to an equivalent msgspec Struct type.
    
    This enables the most optimized serialization path when using msgspec.
    Results are cached for performance.
    
    Args:
        model_type: The Pydantic model type to convert
        
    Returns:
        An equivalent msgspec Struct type
    """
    if model_type not in _STRUCT_CACHE:
        # Create a msgspec Struct type with the same fields as the Pydantic model
        fields = {}
        for name, field in model_type.model_fields.items():
            annotation = field.annotation
            default = field.default if field.default is not None else msgspec.NODEFAULT
            fields[name] = (annotation, default)
        
        # Create a new msgspec Struct type
        struct_type = msgspec.Struct.create(
            fields, 
            name=model_type.__name__,
            gc=False,  # Disable GC for better performance
        )
        _STRUCT_CACHE[model_type] = struct_type
    
    return _STRUCT_CACHE[model_type]


def optimized_model_dumps(model: BaseModel) -> bytes:
    """
    Serialize a Pydantic model to bytes using the most optimized method available.
    
    This will try to use msgspec Structs for the highest performance when possible.
    
    Args:
        model: The Pydantic model to serialize
        
    Returns:
        The serialized data as bytes
    """
    # Convert the model to a dict for serialization
    model_dict = model.model_dump(by_alias=True, mode="json", exclude_none=True)
    
    # Use msgspec for the fastest possible serialization
    return msgspec.json.encode(model_dict)


def optimized_model_loads(data: bytes, model_type: Type[T]) -> T:
    """
    Deserialize bytes to a Pydantic model using the most optimized method available.
    
    This will try to use msgspec Structs for the highest performance when possible.
    
    Args:
        data: The data to deserialize
        model_type: The Pydantic model type to deserialize into
        
    Returns:
        The deserialized Pydantic model
    """
    # Fastest path: decode directly to a dict
    dict_data = msgspec.json.decode(data)
    
    # Then convert to the Pydantic model
    return model_type.model_validate(dict_data) 