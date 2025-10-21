import pytest
import time
from src.engine.core.matching_engine import MatchingEngine

class TestPerformance:
    
    def test_throughput(self):
        """Test system can handle high order throughput"""
        engine = MatchingEngine()
        start_time = time.time()
        order_count = 1000
        
        for i in range(order_count):
            engine.submit_order({
                "symbol": "BTC-USDT",
                "order_type": "limit",
                "side": "buy" if i % 2 == 0 else "sell",
                "quantity": "1.0",
                "price": str(50000 + (i % 100))
            })
        
        elapsed = time.time() - start_time
        throughput = order_count / elapsed
        
        assert throughput > 100, f"Throughput too low: {throughput:.2f} orders/sec"
        print(f"Throughput: {throughput:.2f} orders/sec")
    
    def test_latency(self):
        """Test order processing latency"""
        engine = MatchingEngine()
        latencies = []
        
        # Warm up
        for _ in range(100):
            engine.submit_order({
                "symbol": "BTC-USDT", "order_type": "limit", "side": "buy",
                "quantity": "1.0", "price": "50000"
            })
        
        # Measure latency
        for _ in range(1000):
            start = time.perf_counter()
            engine.submit_order({
                "symbol": "BTC-USDT", "order_type": "limit", "side": "sell", 
                "quantity": "1.0", "price": "50001"
            })
            latency = (time.perf_counter() - start) * 1_000_000  # microseconds
            latencies.append(latency)
        
        avg_latency = sum(latencies) / len(latencies)
        assert avg_latency < 10_000, f"Latency too high: {avg_latency:.2f}μs"
        print(f"Average latency: {avg_latency:.2f}μs")