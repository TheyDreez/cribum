import time
from backend.services.rules_engine import RulesEngine

def run_benchmark(iterations: int = 20000):
    engine = RulesEngine()

    test_cases = [
        # Case 1: Match A and B
        [
            {"text": "Losartana 50mg", "score": 0.85},
            {"text": "Lorazepam 2mg", "score": 0.75},
        ],
        # Case 2: Match via keywords/brands
        [
            {"text": "losartan potassium 50mg", "score": 0.80},
            {"text": "lorazepan 2mg tab", "score": 0.70},
        ],
        # Case 3: Match A only
        [
            {"text": "Losartana 50mg", "score": 0.90},
            {"text": "Aspirina 100mg", "score": 0.60},
        ],
        # Case 4: No match in LASA database
        [
            {"text": "Amoxicilina 500mg", "score": 0.95},
            {"text": "Ibuprofeno 600mg", "score": 0.80},
            {"text": "Paracetamol 750mg", "score": 0.50},
        ],
        # Case 5: Match Citalopram / Escitalopram
        [
            {"text": "Citalopram 20mg", "score": 0.88},
            {"text": "Escitalopram 10mg", "score": 0.77},
        ],
    ]

    start_time = time.perf_counter()
    for _ in range(iterations):
        for case in test_cases:
            engine._check_lasa_collision(case)
    end_time = time.perf_counter()

    total_calls = iterations * len(test_cases)
    elapsed = end_time - start_time
    ops_per_sec = total_calls / elapsed
    time_per_op_us = (elapsed / total_calls) * 1e6

    print(f"Benchmark completed:")
    print(f"Total calls: {total_calls}")
    print(f"Total time: {elapsed:.4f} seconds")
    print(f"Operations/sec: {ops_per_sec:.2f}")
    print(f"Avg time per operation: {time_per_op_us:.2f} µs")

if __name__ == "__main__":
    run_benchmark()
