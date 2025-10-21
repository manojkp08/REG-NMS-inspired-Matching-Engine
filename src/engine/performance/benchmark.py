import time
import statistics
from contextlib import contextmanager
from typing import List, Dict, Any
from decimal import Decimal

@contextmanager
def benchmark_operation(name: str):
    """Context manager to measure operation latency"""
    start = time.perf_counter_ns()
    yield
    elapsed = (time.perf_counter_ns() - start) / 1000  # microseconds
    print(f"⏱️  {name}: {elapsed:.2f}μs")

class PerformanceTracker:
    def __init__(self):
        self.metrics = {
            "order_processing": [],
            "matching_engine": [],
            "trade_generation": [],
            "bbo_calculation": []
        }
    
    def record_metric(self, category: str, latency_us: float):
        if category in self.metrics:
            self.metrics[category].append(latency_us)
    
    def get_summary(self) -> Dict[str, Any]:
        summary = {}
        for category, latencies in self.metrics.items():
            if latencies:
                summary[category] = {
                    "count": len(latencies),
                    "min": min(latencies),
                    "max": max(latencies),
                    "mean": statistics.mean(latencies),
                    "median": statistics.median(latencies),
                    "p95": sorted(latencies)[int(len(latencies) * 0.95)],
                    "p99": sorted(latencies)[int(len(latencies) * 0.99)]
                }
        return summary

# Global performance tracker
perf_tracker = PerformanceTracker()