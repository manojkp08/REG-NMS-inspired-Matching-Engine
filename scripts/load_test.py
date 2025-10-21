import time
import requests
import threading
from concurrent.futures import ThreadPoolExecutor
from statistics import mean, median

API_BASE = "http://localhost:8000/api/v1"

def submit_single_order(order_id):
    """Submit a single order and return latency"""
    start_time = time.perf_counter()
    
    try:
        response = requests.post(f"{API_BASE}/orders", json={
            "symbol": "BTC-USDT",
            "order_type": "limit",
            "side": "buy" if order_id % 2 == 0 else "sell",
            "quantity": "1.0",
            "price": str(50000 + (order_id % 100))
        }, timeout=1.0)
        
        latency = (time.perf_counter() - start_time) * 1_000_000  # microseconds
        return latency, response.status_code == 200
        
    except Exception as e:
        return None, False

def run_throughput_test(num_orders=1000):
    """Test order throughput"""
    print(f"🚀 Running throughput test with {num_orders} orders...")
    
    start_time = time.time()
    successful_orders = 0
    
    for i in range(num_orders):
        latency, success = submit_single_order(i)
        if success:
            successful_orders += 1
    
    elapsed = time.time() - start_time
    throughput = successful_orders / elapsed
    
    print(f"✅ Throughput Results:")
    print(f"   Orders: {successful_orders}/{num_orders}")
    print(f"   Time: {elapsed:.2f}s")
    print(f"   Throughput: {throughput:.2f} orders/sec")
    
    return throughput > 100  # Target: 100+ orders/sec

def run_concurrent_test(num_threads=10, orders_per_thread=100):
    """Test concurrent order submission"""
    print(f"🧵 Running concurrent test: {num_threads} threads, {orders_per_thread} orders each...")
    
    def worker(thread_id):
        latencies = []
        for i in range(orders_per_thread):
            latency, success = submit_single_order(thread_id * 1000 + i)
            if latency:
                latencies.append(latency)
        return latencies
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        results = list(executor.map(worker, range(num_threads)))
    
    elapsed = time.time() - start_time
    total_orders = num_threads * orders_per_thread
    
    # Flatten all latencies
    all_latencies = []
    for latencies in results:
        all_latencies.extend(latencies)
    
    if all_latencies:
        print(f"✅ Concurrent Test Results:")
        print(f"   Total Orders: {len(all_latencies)}")
        print(f"   Time: {elapsed:.2f}s")
        print(f"   Avg Latency: {mean(all_latencies):.2f}μs")
        print(f"   Median Latency: {median(all_latencies):.2f}μs")
        print(f"   Min Latency: {min(all_latencies):.2f}μs")
        print(f"   Max Latency: {max(all_latencies):.2f}μs")
    
    return len(all_latencies) > total_orders * 0.9  # 90% success rate

if __name__ == "__main__":
    print("📊 GoQuant Matching Engine - Load Testing")
    print("=" * 50)
    
    # Wait for server to start
    time.sleep(2)
    
    # Run tests
    throughput_ok = run_throughput_test(1000)
    concurrent_ok = run_concurrent_test(5, 200)
    
    print("\n📈 Load Test Summary:")
    print(f"   Throughput Test: {'✅ PASS' if throughput_ok else '❌ FAIL'}")
    print(f"   Concurrent Test: {'✅ PASS' if concurrent_ok else '❌ FAIL'}")
    
    if throughput_ok and concurrent_ok:
        print("🎉 All load tests passed!")
    else:
        print("💥 Some tests failed - check system performance")