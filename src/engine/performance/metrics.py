import time
from datetime import datetime
from typing import Dict, List
from statistics import mean, median

class PerformanceMetrics:
    def __init__(self):
        self.order_latencies: List[float] = []
        self.trade_latencies: List[float] = []
        self.start_time = datetime.utcnow()
        self.orders_processed = 0
        self.trades_executed = 0
    
    def record_order_latency(self, latency_microseconds: float):
        """Record order processing latency"""
        self.order_latencies.append(latency_microseconds)
        self.orders_processed += 1
    
    def record_trade_latency(self, latency_microseconds: float):
        """Record trade execution latency"""
        self.trade_latencies.append(latency_microseconds)
        self.trades_executed += 1
    
    def get_summary(self) -> Dict:
        """Get performance summary"""
        if not self.order_latencies:
            return {}
        
        sorted_latencies = sorted(self.order_latencies)
        n = len(sorted_latencies)
        
        return {
            "orders_processed": self.orders_processed,
            "trades_executed": self.trades_executed,
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "order_latency_us": {
                "min": min(self.order_latencies),
                "max": max(self.order_latencies),
                "mean": mean(self.order_latencies),
                "median": median(self.order_latencies),
                "p90": sorted_latencies[int(n * 0.9)],
                "p95": sorted_latencies[int(n * 0.95)],
                "p99": sorted_latencies[int(n * 0.99)],
            },
            "throughput_ops_sec": self.orders_processed / (datetime.utcnow() - self.start_time).total_seconds()
        }