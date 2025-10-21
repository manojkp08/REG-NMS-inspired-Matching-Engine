import json
from datetime import datetime
import os
from typing import Dict, Any

class SnapshotManager:
    """Simple snapshot manager for order book state"""
    
    def __init__(self, snapshot_dir: str = "data/snapshots"):
        self.snapshot_dir = snapshot_dir
    
    def take_snapshot(self, order_books: Dict[str, Any]) -> str:
        """Take snapshot of all order books"""
        snapshot = {
            "timestamp": datetime.utcnow().isoformat(),
            "order_books": {}
        }
        
        for symbol, order_book in order_books.items():
            snapshot["order_books"][symbol] = {
                "bids": self._serialize_side(order_book.bids),
                "asks": self._serialize_side(order_book.asks)
            }
        
        # Save to file
        filename = f"{self.snapshot_dir}/snapshot_{int(datetime.now().timestamp())}.json"
        with open(filename, 'w') as f:
            json.dump(snapshot, f, indent=2)
        
        return filename
    
    def _serialize_side(self, side_data):
        """Serialize order book side for snapshot"""
        serialized = {}
        for price, orders in side_data.items():
            serialized[str(price)] = [order.to_dict() for order in orders]
        return serialized
    
    def load_snapshot(self, filename: str) -> Dict[str, Any]:
        """Load order book snapshot from file"""
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        

    def get_latest_snapshot(self) -> str:
        """Get the most recent snapshot file"""
        try:
            files = [f for f in os.listdir(self.snapshot_dir) if f.startswith("snapshot_")]
            if not files:
                return ""
            latest = max(files)
            return os.path.join(self.snapshot_dir, latest)
        except Exception:
            return ""

    def cleanup_old_snapshots(self, keep_count: int = 5):
        """Keep only recent snapshots"""
        try:
            files = [f for f in os.listdir(self.snapshot_dir) if f.startswith("snapshot_")]
            if len(files) <= keep_count:
                return
                
            # Sort by timestamp and remove old ones
            files_sorted = sorted(files)
            for old_file in files_sorted[:-keep_count]:
                os.remove(os.path.join(self.snapshot_dir, old_file))
        except Exception as e:
            print(f"Snapshot cleanup error: {e}")