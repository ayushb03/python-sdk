"""
FlatBuffers serialization for MCP messages.

This module provides high-performance serialization using FlatBuffers.
"""

import json
import logging
from typing import Any, Dict, Optional, Type, TypeVar, Union, cast

try:
    import flatbuffers
    _FLATBUFFERS_AVAILABLE = True
except ImportError:
    _FLATBUFFERS_AVAILABLE = False

import mcp.types as types
from mcp.shared.serialization import dumps

# Type variable for generic functions
T = TypeVar("T")

# Logger for this module
logger = logging.getLogger(__name__)


def flatbuffers_available() -> bool:
    """Check if FlatBuffers is available on the system."""
    return _FLATBUFFERS_AVAILABLE


def serialize_message(message: types.JSONRPCMessage) -> bytes:
    """
    Serialize an MCP message using FlatBuffers.
    
    Args:
        message: The MCP message to serialize
        
    Returns:
        The serialized data as bytes
    """
    if not _FLATBUFFERS_AVAILABLE:
        raise ImportError("FlatBuffers is not available. Install it with 'pip install flatbuffers'")
    
    # Create a FlatBuffers builder
    builder = flatbuffers.Builder(1024)
    
    # Get JSON representation for compatibility with fields we don't directly encode
    message_dict = message.model_dump(by_alias=True, mode="json", exclude_none=True)
    
    # Create FlatBuffers message based on message type
    if isinstance(message.root, types.JSONRPCRequest):
        return _serialize_request(builder, message.root, message_dict)
    elif isinstance(message.root, types.JSONRPCResponse):
        return _serialize_response(builder, message.root, message_dict)
    elif isinstance(message.root, types.JSONRPCNotification):
        return _serialize_notification(builder, message.root, message_dict)
    elif isinstance(message.root, types.JSONRPCError):
        return _serialize_error(builder, message.root, message_dict)
    else:
        # Fallback to JSON if we can't determine the message type
        logger.warning(f"Unknown message type: {type(message.root)}. Falling back to JSON serialization.")
        return dumps(message_dict)


def deserialize_message(data: bytes) -> types.JSONRPCMessage:
    """
    Deserialize FlatBuffers data to an MCP message.
    
    Args:
        data: The FlatBuffers data to deserialize
        
    Returns:
        The deserialized MCP message
    """
    if not _FLATBUFFERS_AVAILABLE:
        raise ImportError("FlatBuffers is not available. Install it with 'pip install flatbuffers'")
    
    try:
        # Check if the data is a valid FlatBuffers message
        # This is a simple heuristic - real implementation would use proper FlatBuffers methods
        if len(data) < 4 or not data.startswith(b'FLAT'):
            # If it doesn't look like a FlatBuffers message, try JSON
            return types.JSONRPCMessage.model_validate_json(data)
        
        # For now, we'll implement a simplified version that decodes to JSON first,
        # then uses Pydantic for the final model validation
        # In a full implementation, this would directly construct the appropriate objects
        
        # Extract the JSON fields from the FlatBuffers message
        json_data = _extract_json_from_flatbuffers(data)
        
        # Use Pydantic to validate and build the proper object
        return types.JSONRPCMessage.model_validate(json_data)
    
    except Exception as e:
        # If FlatBuffers deserialization fails, try JSON as fallback
        logger.warning(f"FlatBuffers deserialization failed: {e}. Trying JSON fallback.")
        return types.JSONRPCMessage.model_validate_json(data)


# Helper Functions for serialization

def _serialize_request(builder: 'flatbuffers.Builder', 
                       request: types.JSONRPCRequest, 
                       message_dict: Dict[str, Any]) -> bytes:
    """Serialize a request message to FlatBuffers."""
    # For now, we implement a compatibility layer that still uses JSON internally
    # A full implementation would serialize the entire structure to FlatBuffers
    
    # Add a FlatBuffers header so we can identify our messages
    header = builder.CreateString("FLAT")
    
    # Serialize the whole message to JSON for now - in a real implementation,
    # we would build the proper FlatBuffers objects
    json_encoded = json.dumps(message_dict).encode('utf-8')
    json_vector = builder.CreateByteVector(json_encoded)
    
    # Build a simple container for our data
    builder.StartObject(2)
    builder.PrependUOffsetTRelative(0, header)
    builder.PrependUOffsetTRelative(1, json_vector)
    message = builder.EndObject()
    
    builder.Finish(message)
    return builder.Output()


def _serialize_response(builder: 'flatbuffers.Builder', 
                        response: types.JSONRPCResponse, 
                        message_dict: Dict[str, Any]) -> bytes:
    """Serialize a response message to FlatBuffers."""
    # Similar to request serialization - for full implementation
    return _serialize_request(builder, cast(types.JSONRPCRequest, response), message_dict)


def _serialize_notification(builder: 'flatbuffers.Builder', 
                           notification: types.JSONRPCNotification, 
                           message_dict: Dict[str, Any]) -> bytes:
    """Serialize a notification message to FlatBuffers."""
    # Similar to request serialization - for full implementation
    return _serialize_request(builder, cast(types.JSONRPCRequest, notification), message_dict)


def _serialize_error(builder: 'flatbuffers.Builder', 
                     error: types.JSONRPCError, 
                     message_dict: Dict[str, Any]) -> bytes:
    """Serialize an error message to FlatBuffers."""
    # Similar to request serialization - for full implementation 
    return _serialize_request(builder, cast(types.JSONRPCRequest, error), message_dict)


def _extract_json_from_flatbuffers(data: bytes) -> Dict[str, Any]:
    """
    Extract JSON data from a FlatBuffers message.
    
    This is a simplified implementation for compatibility.
    """
    # Skip the "FLAT" header (first 4 bytes)
    json_data = data[4:]
    
    # Find where the JSON payload begins
    start_index = 0
    for i in range(len(json_data)):
        if json_data[i:i+1] == b'{':
            start_index = i
            break
    
    # Extract and parse the JSON payload
    json_payload = json_data[start_index:]
    return json.loads(json_payload)