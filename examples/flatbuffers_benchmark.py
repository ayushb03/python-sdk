import time
import json
from typing import Any, Dict, List, Optional

import mcp.types as types
from mcp.shared.config import configure, SerializationFormat
from mcp.shared.serialization import dumps, loads, model_dumps, model_loads


def benchmark_serialization(name: str, data: Any, iterations: int = 10000):
    """
    Benchmark serialization performance for all formats.
    
    Args:
        name: The name of the benchmark
        data: The data to serialize/deserialize
        iterations: The number of iterations to run
    """
    # Standard JSON (using Pydantic model_dumps if needed)
    start_time = time.time()
    for _ in range(iterations):
        if isinstance(data, types.JSONRPCMessage):
            # Handle JSONRPCMessage directly with its optimized serialization
            json_str = data.model_dump_json()
            # We don't deserialize here since the comparison would be unfair
            # (other formats do full serialization-deserialization cycles)
        elif hasattr(data, 'model_dump_json'):
            # Handle other Pydantic models
            json_str = data.model_dump_json()
            # For simplicity, we'll convert to dict for deserialization
            json_dict = json.loads(json_str)
        else:
            json_str = json.dumps(data)
            json_dict = json.loads(json_str)
    json_time = time.time() - start_time
    
    # ORJSON
    configure(serialization_format=SerializationFormat.ORJSON)
    start_time = time.time()
    for _ in range(iterations):
        try:
            serialized = dumps(data)
            loads(serialized)
        except Exception as e:
            print(f"ORJSON error: {e}")
            break
    orjson_time = time.time() - start_time
    
    # MSGPACK
    configure(serialization_format=SerializationFormat.MSGPACK)
    start_time = time.time()
    for _ in range(iterations):
        try:
            serialized = dumps(data)
            loads(serialized)
        except Exception as e:
            print(f"MSGPACK error: {e}")
            break
    msgpack_time = time.time() - start_time
    
    # MSGSPEC
    configure(serialization_format=SerializationFormat.MSGSPEC)
    start_time = time.time()
    for _ in range(iterations):
        try:
            serialized = dumps(data)
            loads(serialized)
        except Exception as e:
            print(f"MSGSPEC error: {e}")
            break
    msgspec_time = time.time() - start_time
    
    # FLATBUFFERS
    try:
        configure(serialization_format=SerializationFormat.FLATBUFFERS)
        start_time = time.time()
        for _ in range(iterations):
            try:
                serialized = dumps(data)
                loads(serialized)
            except Exception as e:
                print(f"FLATBUFFERS error: {e}")
                break
        flatbuffers_time = time.time() - start_time
        flatbuffers_available = True
    except ImportError:
        flatbuffers_time = float('inf')
        flatbuffers_available = False
    
    # Print results
    print(f"\n=== {name} Benchmark ({iterations} iterations) ===")
    print(f"Standard JSON: {json_time:.4f}s (baseline)")
    print(f"ORJSON: {orjson_time:.4f}s ({json_time/orjson_time:.1f}x faster)")
    print(f"MSGPACK: {msgpack_time:.4f}s ({json_time/msgpack_time:.1f}x faster)")
    print(f"MSGSPEC: {msgspec_time:.4f}s ({json_time/msgspec_time:.1f}x faster)")
    
    if flatbuffers_available:
        print(f"FLATBUFFERS: {flatbuffers_time:.4f}s ({json_time/flatbuffers_time:.1f}x faster)")
    else:
        print("FLATBUFFERS: Not available. Install with 'pip install flatbuffers'")


def benchmark_jsonrpc_message(iterations: int = 1000):
    """
    Benchmark JSON-RPC message serialization where FlatBuffers should excel.
    
    Args:
        iterations: The number of iterations to run
    """
    # Create a request message
    request = types.JSONRPCMessage(
        types.JSONRPCRequest(
            jsonrpc="2.0",
            id="1",
            method="resources/read",
            params={
                "uri": "file:///tmp/example.txt",
                "_meta": {
                    "progressToken": "token123"
                }
            }
        )
    )
    
    # Create a response message
    response = types.JSONRPCMessage(
        types.JSONRPCResponse(
            jsonrpc="2.0",
            id="1",
            result={
                "contents": [
                    {
                        "uri": "file:///tmp/example.txt",
                        "text": "Hello, world!",
                        "mimeType": "text/plain"
                    }
                ],
                "_meta": {
                    "timing": 0.123
                }
            }
        )
    )
    
    # Create an error message
    error = types.JSONRPCMessage(
        types.JSONRPCError(
            jsonrpc="2.0",
            id="1",
            error={
                "code": -32600,
                "message": "Invalid Request",
                "data": {
                    "details": "The request was malformed"
                }
            }
        )
    )
    
    print("\n=== JSON-RPC Message Benchmarks ===")
    
    # Using a smaller number of iterations for structured messages
    benchmark_serialization("JSON-RPC Request", request, iterations)
    benchmark_serialization("JSON-RPC Response", response, iterations)
    benchmark_serialization("JSON-RPC Error", error, iterations)


def main():
    """Run the benchmarks."""
    print("MCP SDK FlatBuffers Benchmark")
    print("=============================")
    
    # Simple data
    simple_data = {
        "name": "Example",
        "value": 42,
        "enabled": True,
        "tags": ["performance", "optimization"],
    }
    benchmark_serialization("Simple Data", simple_data)
    
    # Complex data
    complex_data = {
        "message": {
            "id": "1234567890",
            "method": "example",
            "params": {
                "name": "Example",
                "values": [1, 2, 3, 4, 5],
                "metadata": {
                    "created_at": "2023-01-01T00:00:00Z",
                    "updated_at": "2023-01-02T00:00:00Z",
                    "tags": ["performance", "optimization", "example"],
                },
                "options": {
                    "feature1": True,
                    "feature2": False,
                    "feature3": True,
                },
            },
        }
    }
    benchmark_serialization("Complex Data", complex_data)
    
    # JSON-RPC message benchmarks
    benchmark_jsonrpc_message()
    
    # Restore default configuration
    configure(serialization_format=SerializationFormat.ORJSON)
    print("\nDefaults restored. Using ORJSON as the default serialization format.")


if __name__ == "__main__":
    main()