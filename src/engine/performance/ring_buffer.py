import threading
from typing import Any, Optional

class RingBuffer:
    """Simple lock-free ring buffer for order ingestion"""
    
    def __init__(self, size: int = 10000):
        self.size = size
        self.buffer = [None] * size
        self.write_index = 0
        self.read_index = 0
        self.lock = threading.Lock()
    
    def push(self, item: Any) -> bool:
        """Push item to buffer, returns True if successful"""
        with self.lock:
            next_index = (self.write_index + 1) % self.size
            if next_index == self.read_index:
                return False  # Buffer full
            
            self.buffer[self.write_index] = item
            self.write_index = next_index
            return True
    
    def pop(self) -> Optional[Any]:
        """Pop item from buffer, returns None if empty"""
        with self.lock:
            if self.read_index == self.write_index:
                return None  # Buffer empty
            
            item = self.buffer[self.read_index]
            self.read_index = (self.read_index + 1) % self.size
            return item
    
    def is_empty(self) -> bool:
        """Check if buffer is empty"""
        return self.read_index == self.write_index
    
    def is_full(self) -> bool:
        """Check if buffer is full"""
        return (self.write_index + 1) % self.size == self.read_index