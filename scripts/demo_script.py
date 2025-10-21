import requests
import asyncio
import websockets
import json
import time
from decimal import Decimal

API_BASE = "http://localhost:8000/api/v1"

def print_step(step, description):
    print(f"\n{'='*50}")
    print(f"STEP {step}: {description}")
    print(f"{'='*50}")

def submit_order(symbol, order_type, side, quantity, price=None):
    """Submit order to REST API"""
    payload = {
        "symbol": symbol,
        "order_type": order_type,
        "side": side,
        "quantity": str(quantity)
    }
    if price is not None:
        payload["price"] = str(price)
    
    response = requests.post(f"{API_BASE}/orders", json=payload)
    return response.json()

def get_orderbook(symbol):
    """Get order book snapshot"""
    response = requests.get(f"{API_BASE}/orderbook/{symbol}")
    return response.json()

async def listen_trades():
    """Listen to trade WebSocket feed"""
    print("Listening to trade feed...")
    try:
        async with websockets.connect("ws://localhost:8080/ws/trades") as websocket:
            # Wait for trades for 10 seconds
            for _ in range(10):
                message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                trade = json.loads(message)
                if trade["type"] == "trade":
                    print(f"🔔 TRADE: {trade['quantity']} BTC @ ${trade['price']} "
                          f"({trade['aggressor_side']})")
    except asyncio.TimeoutError:
        print("No more trades received")

def run_demo():
    """Run complete demo sequence"""
    print("🚀 GoQuant Matching Engine - Live Demo")
    
    # Step 1: Populate initial orders
    print_step(1, "Populating Order Book")
    
    # Sell side (asks)
    print("Placing SELL orders:")
    submit_order("BTC-USDT", "limit", "sell", 1.0, 50100)  # Charlie
    submit_order("BTC-USDT", "limit", "sell", 1.5, 50200)  # David
    submit_order("BTC-USDT", "limit", "sell", 0.5, 50000)  # Bob (best price)
    
    # Buy side (bids)  
    print("Placing BUY orders:")
    submit_order("BTC-USDT", "limit", "buy", 2.0, 49900)  # Alice
    submit_order("BTC-USDT", "limit", "buy", 1.0, 49800)  # Eve
    
    # Show order book
    book = get_orderbook("BTC-USDT")
    print("\n📊 Initial Order Book:")
    print("BIDS (Buyers):")
    for bid in book["bids"][:5]:
        print(f"  ${bid[0]} - {bid[1]} BTC")
    print("ASKS (Sellers):")
    for ask in book["asks"][:5]:
        print(f"  ${ask[0]} - {ask[1]} BTC")
    
    # Step 2: Execute market order
    print_step(2, "Executing Market Order")
    print("Alice places MARKET BUY for 2.5 BTC...")
    
    result = submit_order("BTC-USDT", "market", "buy", 2.5)
    print(f"Result: {result['status']}")
    print(f"Filled: {result['filled_quantity']} BTC")
    print(f"Avg Price: ${result['avg_fill_price']}")
    
    # Step 3: Show updated order book
    print_step(3, "Updated Order Book")
    book = get_orderbook("BTC-USDT")
    print("BIDS (Buyers):")
    for bid in book["bids"][:5]:
        print(f"  ${bid[0]} - {bid[1]} BTC")
    print("ASKS (Sellers):")
    for ask in book["asks"][:5]:
        print(f"  ${ask[0]} - {ask[1]} BTC")
    
    # Step 4: Test IOC order
    print_step(4, "Testing IOC Order")
    print("Bob places IOC BUY for 5 BTC @ $50,000...")
    
    result = submit_order("BTC-USDT", "ioc", "buy", 5.0, 50000)
    print(f"Result: {result['status']}")
    print(f"Filled: {result['filled_quantity']} BTC")
    print(f"Remaining: {result['remaining_quantity']} BTC (cancelled)")
    
    # Step 5: Test FOK order
    print_step(5, "Testing FOK Order") 
    print("Charlie places FOK BUY for 10 BTC @ $50,000...")
    
    result = submit_order("BTC-USDT", "fok", "buy", 10.0, 50000)
    print(f"Result: {result['status']} (rejected - not enough liquidity)")
    
    # Step 6: Listen to live trades
    print_step(6, "Live Trade Feed")
    asyncio.run(listen_trades())
    
    print("\n✅ Demo completed successfully!")

if __name__ == "__main__":
    run_demo()