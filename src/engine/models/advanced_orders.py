from enum import Enum
from decimal import Decimal
from typing import Optional, Callable
from datetime import datetime

class AdvancedOrderType(Enum):
    STOP_LOSS = "stop_loss"
    STOP_LIMIT = "stop_limit"
    TAKE_PROFIT = "take_profit"

class AdvancedOrder:
    def __init__(self, order_id: str, symbol: str, side: str, quantity: Decimal,
                 order_type: AdvancedOrderType, trigger_price: Decimal,
                 limit_price: Optional[Decimal] = None, client_id: Optional[str] = None):
        self.order_id = order_id
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.order_type = order_type
        self.trigger_price = trigger_price
        self.limit_price = limit_price
        self.client_id = client_id
        self.activated = False
        self.create_time = datetime.utcnow()

    def check_trigger(self, current_price: Decimal) -> bool:
        if self.activated:
            return False
        
        if self.side == "buy":
            # For buy orders: trigger when price drops to/below trigger (stop-loss) 
            # or rises to/above trigger (take-profit)
            if self.order_type in [AdvancedOrderType.STOP_LOSS, AdvancedOrderType.STOP_LIMIT]:
                trigger = current_price <= self.trigger_price
            else:  # TAKE_PROFIT
                trigger = current_price >= self.trigger_price
        else:  # sell
            # For sell orders: trigger when price rises to/above trigger (stop-loss)
            # or drops to/below trigger (take-profit)
            if self.order_type in [AdvancedOrderType.STOP_LOSS, AdvancedOrderType.STOP_LIMIT]:
                trigger = current_price >= self.trigger_price
            else:  # TAKE_PROFIT
                trigger = current_price <= self.trigger_price
        
        self.activated = trigger
        return trigger

    def to_limit_order(self) -> dict:
        """Convert to regular limit order when triggered"""
        return {
            "symbol": self.symbol,
            "order_type": "limit" if self.order_type == AdvancedOrderType.STOP_LIMIT else "market",
            "side": self.side,
            "quantity": str(self.quantity),
            "price": str(self.limit_price) if self.limit_price else None,
            "client_id": self.client_id
        }