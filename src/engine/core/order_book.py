from sortedcontainers import SortedDict
from collections import deque
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
import logging

from .order import Order, OrderSide, OrderStatus

logger = logging.getLogger(__name__)

class OrderBook:
    def __init__(self, symbol: str):
        self.symbol = symbol
        # SortedDict: price -> deque of orders (FIFO at each price level)
        self.bids = SortedDict()  # Prices sorted descending
        self.asks = SortedDict()  # Prices sorted ascending
        self.orders: Dict[str, Order] = {}  # order_id -> Order
        self._bbo_dirty = True
        self._cached_bbo = {"best_bid": None, "best_ask": None}
        
    def add_order(self, order: Order) -> None:
        """Add order to the appropriate side of the book"""
        if order.order_id in self.orders:
            raise ValueError(f"Order {order.order_id} already exists")
            
        self.orders[order.order_id] = order
        
        if order.side == OrderSide.BUY:
            book = self.bids
        else:
            book = self.asks
            
        price = order.price
        if price not in book:
            book[price] = deque() #O(n) FIFO per price level
        
        book[price].append(order)
        order.status = OrderStatus.OPEN
        self._bbo_dirty = True
        
        logger.debug(f"Added order {order.order_id} to {order.side} side at price {price}")
    
    def remove_order(self, order_id: str) -> Optional[Order]:
        """Remove order from book by order_id"""
        if order_id not in self.orders:
            return None
            
        order = self.orders[order_id]
        
        if order.side == OrderSide.BUY:
            book = self.bids
        else:
            book = self.asks
            
        price = order.price
        if price in book:
            # Remove from price level queue
            try:
                book[price].remove(order)
            except ValueError:
                logger.warning(f"Order {order_id} not found in price level {price}")
            
            # Remove price level if empty
            if len(book[price]) == 0:
                del book[price]
                
        del self.orders[order_id]
        self._bbo_dirty = True
        
        logger.debug(f"Removed order {order_id} from book")
        return order
    
    def get_best_bid(self) -> Optional[Tuple[Decimal, deque]]:
        """Get best bid price level (highest price)"""
        if not self.bids:
            return None
        return self.bids.peekitem(-1)  # Last item in sorted dict (highest price)
    
    def get_best_ask(self) -> Optional[Tuple[Decimal, deque]]:
        """Get best ask price level (lowest price)"""
        if not self.asks:
            return None
        return self.bids.peekitem(0)  # First item in sorted dict (lowest price)
    
    def get_bbo(self) -> dict:
        """Get Best Bid/Offer in O(1) with lazy calculation"""
        if self._bbo_dirty:
            self._recalculate_bbo()
            
        return self._cached_bbo.copy()
    
    def _recalculate_bbo(self) -> None:
        """Recalculate BBO (called only when book changes)"""
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()
        
        self._cached_bbo = {
            "best_bid": best_bid[0] if best_bid else None,
            "best_bid_qty": sum(order.remaining_qty for order in best_bid[1]) if best_bid else Decimal('0'),
            "best_ask": best_ask[0] if best_ask else None,
            "best_ask_qty": sum(order.remaining_qty for order in best_ask[1]) if best_ask else Decimal('0'),
        }
        
        # Calculate spread
        if best_bid and best_ask:
            spread = best_ask[0] - best_bid[0]
            self._cached_bbo["spread"] = spread
            self._cached_bbo["spread_bps"] = float((spread / best_bid[0]) * 10000)
        else:
            self._cached_bbo["spread"] = None
            self._cached_bbo["spread_bps"] = None
            
        self._bbo_dirty = False
    
    def get_depth(self, levels: int = 10) -> dict:
        """Get top N price levels for bids and asks"""
        # Bids: highest prices first (last items in sorted dict)
        bid_levels = []
        for i in range(min(levels, len(self.bids))):
            price, orders = self.bids.peekitem(len(self.bids) - 1 - i)
            total_qty = sum(order.remaining_qty for order in orders)
            bid_levels.append([str(price), str(total_qty)])
        
        # Asks: lowest prices first (first items in sorted dict)
        ask_levels = []
        for i in range(min(levels, len(self.asks))):
            price, orders = self.asks.peekitem(i)
            total_qty = sum(order.remaining_qty for order in orders)
            ask_levels.append([str(price), str(total_qty)])
            
        return {
            "bids": bid_levels,
            "asks": ask_levels
        }
    
    def get_orders_at_price(self, side: OrderSide, price: Decimal) -> Optional[deque]:
        """Get all orders at specific price level"""
        if side == OrderSide.BUY:
            return self.bids.get(price)
        else:
            return self.asks.get(price)
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        return self.orders.get(order_id)
    
    def get_total_volume(self) -> dict:
        """Get total volume on each side"""
        bid_volume = sum(
            sum(order.remaining_qty for order in orders)
            for orders in self.bids.values()
        )
        ask_volume = sum(
            sum(order.remaining_qty for order in orders)
            for orders in self.asks.values()
        )
        
        return {
            "bid_volume": bid_volume,
            "ask_volume": ask_volume,
            "total_volume": bid_volume + ask_volume
        }
    
    def __repr__(self) -> str:
        bbo = self.get_bbo()
        return (f"OrderBook(symbol={self.symbol}, bids={len(self.bids)} levels, "
                f"asks={len(self.asks)} levels, BBO={bbo['best_bid']}/{bbo['best_ask']})")