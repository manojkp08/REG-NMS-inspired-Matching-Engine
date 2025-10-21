import json
import time
from datetime import datetime
from typing import Any, Dict

class WriteAheadLog:
    """Simple Write-Ahead Logger for crash recovery"""
    
    def __init__(self, filepath: str = "data/wal/orders.log"):
        self.filepath = filepath
        self._ensure_directory()
        
    def _ensure_directory(self):
        """Create WAL directory if it doesn't exist"""
        import os
        os.makedirs("data/wal", exist_ok=True)
    
    def log_order_submission(self, order: Any) -> None:
        """Log order submission"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "ORDER_SUBMIT",
            "data": {
                "order_id": order.order_id,
                "symbol": order.symbol,
                "side": order.side.value,
                "order_type": order.type.value,
                "price": str(order.price) if order.price else None,
                "quantity": str(order.quantity),
                "client_id": order.client_id
            }
        }
        self._write_entry(entry)
    
    def log_trade(self, trade: Any) -> None:
        """Log trade execution"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "TRADE_EXECUTE", 
            "data": {
                "trade_id": trade.trade_id,
                "symbol": trade.symbol,
                "price": str(trade.price),
                "quantity": str(trade.quantity),
                "maker_order_id": trade.maker_order_id,
                "taker_order_id": trade.taker_order_id
            }
        }
        self._write_entry(entry)
    
    def log_order_cancel(self, order_id: str) -> None:
        """Log order cancellation"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "ORDER_CANCEL",
            "data": {"order_id": order_id}
        }
        self._write_entry(entry)
    
    def _write_entry(self, entry: dict) -> None:
        """Write entry to WAL file"""
        try:
            with open(self.filepath, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"WAL write error: {e}")  # Simple error handling
    
    def replay(self, since_timestamp: str = None) -> list:
        """Replay WAL entries (simplified)"""
        entries = []
        try:
            with open(self.filepath, "r") as f:
                for line in f:
                    entry = json.loads(line.strip())
                    if since_timestamp and entry["timestamp"] < since_timestamp:
                        continue
                    entries.append(entry)
        except FileNotFoundError:
            pass  # No WAL file yet
        return entries
    
    def recover_order_book(self, matching_engine) -> Dict[str, Any]:
        """Recover order book state from WAL"""
        print("🔄 Recovering order book from WAL...")
        
        entries = self.replay()
        recovered_orders = 0
        recovered_trades = 0
        
        for entry in entries:
            try:
                if entry["type"] == "ORDER_SUBMIT":
                    order_data = entry["data"]
                    # Re-create and submit order
                    matching_engine.submit_order(order_data)
                    recovered_orders += 1
                    
                elif entry["type"] == "TRADE_EXECUTE":
                    recovered_trades += 1
                    
            except Exception as e:
                print(f"⚠️ Recovery error: {e}")
        
        print(f"✅ Recovery complete: {recovered_orders} orders, {recovered_trades} trades")
        return {"orders": recovered_orders, "trades": recovered_trades}