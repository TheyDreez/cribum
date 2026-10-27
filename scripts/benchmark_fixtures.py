import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.provider import DemoFixtureProvider


def run_benchmark(iterations: int = 1000):
    print(f"Running benchmark with {iterations} fixture load iterations...")

    # Warmup
    p = DemoFixtureProvider()
    p._load_fixtures()

    start = time.perf_counter()
    for _ in range(iterations):
        provider = DemoFixtureProvider()
        provider._load_fixtures()
    elapsed = time.perf_counter() - start

    avg_ms = (elapsed / iterations) * 1000
    ops_per_sec = iterations / elapsed if elapsed > 0 else 0

    print(f"Total time: {elapsed:.4f} seconds")
    print(f"Average latency per load: {avg_ms:.4f} ms")
    print(f"Throughput: {ops_per_sec:.2f} ops/sec")
    return elapsed, avg_ms, ops_per_sec


if __name__ == "__main__":
    run_benchmark(1000)
