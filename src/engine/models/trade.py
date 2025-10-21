from decimal import Decimal
from datetime import datetime
from typing import Optional

class Trade:
    def __init__(self, trade_id: str, timestamp: datetime, symbol: str, 
                 price: Decimal, quantity: Decimal, aggressor_side: str,
                 maker_order_id: str, taker_order_id: str):
        self.trade_id = trade_id
        self.timestamp = timestamp
        self.symbol = symbol
        self.price = price
        self.quantity = quantity
        self.aggressor_side = aggressor_side
        self.maker_order_id = maker_order_id
        self.taker_order_id = taker_order_id
        self.maker_fee = Decimal('0')
        self.taker_fee = Decimal('0')

    def to_dict(self) -> dict:
        return {
            "trade_id": self.trade_id,
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "price": str(self.price),
            "quantity": str(self.quantity),
            "aggressor_side": self.aggressor_side,
            "maker_order_id": self.maker_order_id,
            "taker_order_id": self.taker_order_id,
            "maker_fee": str(self.maker_fee),
            "taker_fee": str(self.taker_fee)
        }

    def __repr__(self):
        return f"Trade({self.trade_id}: {self.quantity}@{self.price})"