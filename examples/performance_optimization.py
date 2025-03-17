#!/usr/bin/env python3
"""
Performance optimization example for the MCP SDK.

This example demonstrates how to configure and use the optimized serialization
options for maximum performance.
"""

import time
import json
from typing import List, Dict, Any

import mcp.types as types
from mcp.shared.config import configure, SerializationFormat
from mcp.shared.serialization import dumps, loads, model_dumps, model_loads


def benchmark_serialization(name: str, data: Any, iterations: int = 10000):
    """
    Benchmark serialization performance.
    
    Args:
        name: The name of the benchmark
        data: The data to serialize/deserialize
        iterations: The number of iterations to run
    """
    # Standard JSON
    start_time = time.time()
    for _ in range(iterations):
        json_str = json.dumps(data)
        json.loads(json_str)
    json_time = time.time() - start_time
    
    # ORJSON
    configure(serialization_format=SerializationFormat.ORJSON)
    start_time = time.time()
    for _ in range(iterations):
        serialized = dumps(data)
        loads(serialized)
    orjson_time = time.time() - start_time
    
    # MSGPACK
    configure(serialization_format=SerializationFormat.MSGPACK)
    start_time = time.time()
    for _ in range(iterations):
        serialized = dumps(data)
        loads(serialized)
    msgpack_time = time.time() - start_time
    
    # MSGSPEC
    configure(serialization_format=SerializationFormat.MSGSPEC)
    start_time = time.time()
    for _ in range(iterations):
        serialized = dumps(data)
        loads(serialized)
    msgspec_time = time.time() - start_time
    
    # Print results
    print(f"\n=== {name} Benchmark ({iterations} iterations) ===")
    print(f"Standard JSON: {json_time:.4f}s (baseline)")
    print(f"ORJSON: {orjson_time:.4f}s ({json_time/orjson_time:.1f}x faster)")
    print(f"MSGPACK: {msgpack_time:.4f}s ({json_time/msgpack_time:.1f}x faster)")
    print(f"MSGSPEC: {msgspec_time:.4f}s ({json_time/msgspec_time:.1f}x faster)")


def benchmark_model_serialization(iterations: int = 10000):
    """
    Benchmark model serialization performance.
    
    Args:
        iterations: The number of iterations to run
    """
    # Create a sample model
    model = types.Resource(
        uri="file:///tmp/example.txt",
        name="Example Resource",
        description="An example resource for benchmarking",
        mimeType="text/plain",
        size=1024,
        annotations=types.Annotations(
            audience=["user", "assistant"],
            priority=0.5
        )
    )
    
    # Standard JSON with Pydantic
    start_time = time.time()
    for _ in range(iterations):
        json_str = model.model_dump_json()
        types.Resource.model_validate_json(json_str)
    json_time = time.time() - start_time
    
    # ORJSON
    configure(serialization_format=SerializationFormat.ORJSON)
    start_time = time.time()
    for _ in range(iterations):
        serialized = model_dumps(model)
        model_loads(serialized, types.Resource)
    orjson_time = time.time() - start_time
    
    # MSGPACK
    configure(serialization_format=SerializationFormat.MSGPACK)
    start_time = time.time()
    for _ in range(iterations):
        serialized = model_dumps(model)
        model_loads(serialized, types.Resource)
    msgpack_time = time.time() - start_time
    
    # MSGSPEC
    configure(serialization_format=SerializationFormat.MSGSPEC)
    start_time = time.time()
    for _ in range(iterations):
        serialized = model_dumps(model)
        model_loads(serialized, types.Resource)
    msgspec_time = time.time() - start_time
    
    # Print results
    print(f"\n=== Model Serialization Benchmark ({iterations} iterations) ===")
    print(f"Standard JSON: {json_time:.4f}s (baseline)")
    print(f"ORJSON: {orjson_time:.4f}s ({json_time/orjson_time:.1f}x faster)")
    print(f"MSGPACK: {msgpack_time:.4f}s ({json_time/msgpack_time:.1f}x faster)")
    print(f"MSGSPEC: {msgspec_time:.4f}s ({json_time/msgspec_time:.1f}x faster)")


def main():
    """Run the performance benchmarks."""
    print("MCP SDK Performance Optimization Example")
    print("=======================================")
    
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
    
    # Model serialization
    benchmark_model_serialization()
    
    # Restore default configuration
    configure(serialization_format=SerializationFormat.ORJSON)
    print("\nDefaults restored. Using ORJSON as the default serialization format.")


if __name__ == "__main__":
    main() 