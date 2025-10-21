import requests
import time

API_BASE = "http://localhost:8000/api/v1"

def test_persistence():
    """Test basic order persistence (simplified)"""
    print("🧪 Testing Order Persistence...")
    
    # Submit some orders
    orders = []
    for i in range(5):
        response = requests.post(f"{API_BASE}/orders", json={
            "symbol": "BTC-USDT",
            "order_type": "limit", 
            "side": "buy" if i % 2 == 0 else "sell",
            "quantity": "1.0",
            "price": str(50000 + i * 10)
        })
        if response.status_code == 200:
            order_data = response.json()
            orders.append(order_data["order_id"])
            print(f"   Created order: {order_data['order_id']}")
    
    # Verify orders exist
    print("   Verifying orders...")
    for order_id in orders:
        response = requests.get(f"{API_BASE}/orders/{order_id}")
        if response.status_code == 200:
            print(f"   ✅ Order {order_id} verified")
        else:
            print(f"   ❌ Order {order_id} not found")
    
    # Check order book state
    response = requests.get(f"{API_BASE}/orderbook/BTC-USDT")
    if response.status_code == 200:
        book = response.json()
        print(f"   Order book has {len(book['bids'])} bids and {len(book['asks'])} asks")
    
    print("✅ Persistence test completed")

if __name__ == "__main__":
    test_persistence()