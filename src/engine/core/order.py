from enum import Enum
from decimal import Decimal
from datetime import datetime
from typing import Optional
import uuid

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    IOC = "ioc"  # Immediate or Cancel
    FOK = "fok"  # Fill or Kill

class OrderStatus(Enum):
    PENDING = "pending"
    OPEN = "open"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    PARTIAL_FILL_CANCELLED = "partial_fill_cancelled"

class Order:
    def __init__(self, order_id: Optional[str] = None):
        self.order_id = order_id or f"ORD-{int(datetime.now().timestamp())}-{uuid.uuid4().hex[:6]}"
        self.symbol: Optional[str] = None
        self.side: Optional[OrderSide] = None
        self.type: Optional[OrderType] = None
        self.price: Optional[Decimal] = None
        self.quantity: Decimal = Decimal('0')
        self.remaining_qty: Decimal = Decimal('0')
        self.filled_qty: Decimal = Decimal('0')
        self.status: OrderStatus = OrderStatus.PENDING
        self.timestamp: datetime = datetime.utcnow()
        self.client_id: Optional[str] = None
        self.create_time: datetime = datetime.utcnow()
        self.update_time: datetime = datetime.utcnow()

    def initialize(self, symbol: str, side: OrderSide, order_type: OrderType, 
                   quantity: Decimal, price: Optional[Decimal] = None, client_id: Optional[str] = None):
        """Initialize order with validation"""
        self.symbol = symbol
        self.side = side
        self.type = order_type
        self.quantity = quantity
        self.remaining_qty = quantity
        self.price = price
        self.client_id = client_id
        
        # Validate market orders don't have price
        if order_type == OrderType.MARKET and price is not None:
            raise ValueError("Market orders cannot have a price")
        
        # Validate limit orders have price
        if order_type != OrderType.MARKET and price is None:
            raise ValueError("Limit orders must have a price")
        
        if quantity <= Decimal('0'):
            raise ValueError("Quantity must be positive")

    def is_marketable(self, opposing_bbo: Optional[Decimal]) -> bool:
        """Check if order can match at current BBO"""
        if opposing_bbo is None:
            return False
            
        if self.type == OrderType.MARKET:
            return True
        
        if self.side == OrderSide.BUY:
            return self.price >= opposing_bbo
        else:  # SELL
            return self.price <= opposing_bbo

    def can_match_at_price(self, price: Decimal) -> bool:
        """Check if order can match at specific price"""
        if self.type == OrderType.MARKET:
            return True
            
        if self.side == OrderSide.BUY:
            return self.price >= price
        else:  # SELL
            return self.price <= price

    def fill(self, quantity: Decimal, price: Decimal) -> None:
        """Execute partial fill on this order"""
        if quantity > self.remaining_qty:
            raise ValueError(f"Cannot fill {quantity}, only {self.remaining_qty} remaining")
        
        self.filled_qty += quantity
        self.remaining_qty -= quantity
        self.update_time = datetime.utcnow()
        
        if self.remaining_qty == Decimal('0'):
            self.status = OrderStatus.FILLED
        else:
            self.status = OrderStatus.PARTIAL

    def cancel(self) -> None:
        """Cancel the order"""
        if self.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED]:
            raise ValueError(f"Cannot cancel order in {self.status} state")
        
        self.status = OrderStatus.CANCELLED
        self.update_time = datetime.utcnow()

    def reject(self) -> None:
        """Reject the order"""
        self.status = OrderStatus.REJECTED
        self.update_time = datetime.utcnow()

    def reset(self) -> None:
        """Reset for object pooling - clear all fields"""
        self.order_id = None
        self.symbol = None
        self.side = None
        self.type = None
        self.price = None
        self.quantity = Decimal('0')
        self.remaining_qty = Decimal('0')
        self.filled_qty = Decimal('0')
        self.status = OrderStatus.PENDING
        self.timestamp = datetime.utcnow()
        self.client_id = None
        self.create_time = datetime.utcnow()
        self.update_time = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side.value if self.side else None,
            "order_type": self.type.value if self.type else None,
            "price": str(self.price) if self.price else None,
            "quantity": str(self.quantity),
            "original_quantity": str(self.quantity),
            "filled_quantity": str(self.filled_qty),
            "remaining_quantity": str(self.remaining_qty),
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "create_time": self.create_time.isoformat(),
            "update_time": self.update_time.isoformat(),
            "client_id": self.client_id
        }

    def __repr__(self) -> str:
        return (f"Order(id={self.order_id}, symbol={self.symbol}, side={self.side}, "
                f"type={self.type}, price={self.price}, qty={self.quantity}, "
                f"filled={self.filled_qty}, status={self.status})")