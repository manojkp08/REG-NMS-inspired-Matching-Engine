import time
from decimal import Decimal
from typing import List, Optional, Dict, Any
import logging
import uuid
from datetime import datetime

from ..persistence.wal import WriteAheadLog

# Import order-related classes and enums
from .order_book import OrderBook
from . import order as order_module  # Import module to avoid circular issues
from ..models.trade import Trade
from ..models.fee_calculator import FeeCalculator
from ..models.advanced_orders import AdvancedOrder, AdvancedOrderType

# Now import the classes we need
Order = order_module.Order
OrderSide = order_module.OrderSide
OrderType = order_module.OrderType
OrderStatus = order_module.OrderStatus

logger = logging.getLogger(__name__)

class MatchingEngine:
    def __init__(self):
        self.order_books: Dict[str, OrderBook] = {}
        self.trade_id_counter = 0
        self.websocket_manager = None
        self.wal = None  # Will be initialized if persistence enabled
        self.trade_history: List[Trade] = []
        self.fee_calculator = FeeCalculator()
        self.advanced_orders: Dict[str, List[AdvancedOrder]] = {}  # symbol -> list of advanced orders
        self.wal = WriteAheadLog()  # Enable WAL
        self.load_recovery_data()   # Load on startup
        
        # Performance metrics
        self.metrics = {
            "orders_processed": 0,
            "trades_executed": 0,
            "total_volume": Decimal('0'),
            "start_time": datetime.utcnow()
        }
    
    def initialize_symbol(self, symbol: str) -> None:
        """Initialize order book for a trading symbol"""
        if symbol not in self.order_books:
            self.order_books[symbol] = OrderBook(symbol)
            logger.info(f"Initialized order book for {symbol}")

    def load_recovery_data(self):
        """Load from WAL and snapshots on startup"""
        try:
            # Try to recover from WAL
            recovery_stats = self.wal.recover_order_book(self)
            print(f"📊 Recovery stats: {recovery_stats}")
        except Exception as e:
           print(f"⚠️ Recovery failed: {e}")

    
    def submit_order(self, order_data: dict) -> dict:
        """Main entry point for order submission"""
        start_time = time.perf_counter()
        
        print(f"DEBUG 1: Starting submit_order")
        
        try:
            # Validate required fields
            required_fields = ["symbol", "order_type", "side", "quantity"]
            for field in required_fields:
                if field not in order_data:
                    raise ValueError(f"Missing required field: {field}")
                
            print(f"DEBUG 2: Validation passed")
            
            symbol = order_data["symbol"]
            self.initialize_symbol(symbol)

            print(f"DEBUG 3: Symbol initialized")
            
            # Create order object
            order = self._create_order_from_data(order_data)

            print(f"DEBUG 4: Order created: {order.order_id}")
            
            # Log to WAL if enabled
            if self.wal:
                print(f"DEBUG 5: About to log to WAL")
                self.wal.log_order_submission(order)
                print(f"DEBUG 6: WAL logged")
            
            # Try to match the order
            trades = self._match_order(order)
            
            # Handle remaining quantity based on order type
            response = self._handle_remaining_quantity(order, trades)
            
            # Update metrics
            self.metrics["orders_processed"] += 1
            if trades:
                self.metrics["trades_executed"] += len(trades)
                self.metrics["total_volume"] += sum(trade.quantity for trade in trades)
            
            # Broadcast updates
            self._broadcast_updates(symbol, trades)
            
            latency = (time.perf_counter() - start_time) * 1_000_000
            logger.info(f"Order {order.order_id} processed in {latency:.2f}μs - "
                       f"Status: {order.status.value}, Trades: {len(trades)}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing order: {e}")
            return {
                "order_id": order_data.get("order_id", "UNKNOWN"),
                "status": "rejected",
                "error": str(e)
            }
    
    def _create_order_from_data(self, order_data: dict) -> Order:
        """Create Order object from request data"""
        order = Order(order_data.get("order_id"))
        
        # Parse side
        side_str = order_data["side"].lower()
        if side_str == "buy":
            side = OrderSide.BUY
        elif side_str == "sell":
            side = OrderSide.SELL
        else:
            raise ValueError(f"Invalid side: {side_str}")
        
        # Parse order type
        type_str = order_data["order_type"].lower()
        if type_str == "market":
            order_type = OrderType.MARKET
        elif type_str == "limit":
            order_type = OrderType.LIMIT
        elif type_str == "ioc":
            order_type = OrderType.IOC
        elif type_str == "fok":
            order_type = OrderType.FOK
        else:
            raise ValueError(f"Invalid order type: {type_str}")
        
        # Parse quantity and price
        quantity = Decimal(str(order_data["quantity"]))
        price = Decimal(str(order_data["price"])) if order_data.get("price") else None
        
        order.initialize(
            symbol=order_data["symbol"],
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            client_id=order_data.get("client_id")
        )
        
        return order
    
    def _match_order(self, order: Order) -> List[Trade]:
        """Core matching algorithm with price-time priority"""
        trades = []
        order_book = self.order_books[order.symbol]
        
        if order.side == OrderSide.BUY:
            opposing_book = order_book.asks
            price_check = lambda order_price, book_price: order_price >= book_price
        else:
            opposing_book = order_book.bids
            price_check = lambda order_price, book_price: order_price <= book_price
        
        remaining_qty = order.remaining_qty
        
        # For FOK orders, check if entire quantity can be filled first
        if order.type == OrderType.FOK:
            if not self._can_fill_completely(order, opposing_book, price_check):
                order.reject()
                return []
        
        # Iterate through price levels (best price first)
        while remaining_qty > Decimal('0') and len(oppsing_boook) > 0:
            # Get best price level
            if order.side == OrderSide.BUY:
                best_price, order_queue = opposing_book.peekitem(0)  # Lowest ask
            else:
                best_price, order_queue = opposing_book.peekitem(-1)  # Highest bid
            
            # Check if incoming order can match at this price
            if order.type != OrderType.MARKET and not price_check(order.price, best_price):
                break  # No more matching possible
            
            # Match with orders at this price level (FIFO)
            while remaining_qty > Decimal('0') and order_queue:
                resting_order = order_queue[0]  # Oldest order at this price
                
                # Calculate fill quantity
                fill_qty = min(remaining_qty, resting_order.remaining_qty)
                
                # Create trade
                trade = self._generate_trade(
                    maker_order=resting_order,
                    taker_order=order,
                    price=best_price,
                    quantity=fill_qty
                )
                trades.append(trade)
                
                # Update quantities
                remaining_qty -= fill_qty
                resting_order.fill(fill_qty, best_price)
                
                # Remove resting order if fully filled
                if resting_order.remaining_qty == Decimal('0'):
                    order_queue.popleft()
                    # Remove from orders dict if fully filled
                    if resting_order.order_id in order_book.orders:
                        del order_book.orders[resting_order.order_id]
            
            # Remove price level if empty
            if len(order_queue) == 0:
                if order.side == OrderSide.BUY:
                    opposing_book.popitem(0)  # Remove lowest ask
                else:
                    opposing_book.popitem(-1)  # Remove highest bid
        
        order.remaining_qty = remaining_qty
        return trades
    
    def _can_fill_completely(self, order: Order, opposing_book: Any, price_check: callable) -> bool:
        """Check if FOK order can be completely filled"""
        if order.type != OrderType.FOK:
            return True
            
        remaining_qty = order.remaining_qty
        temp_opposing_book = opposing_book.copy()
        
        while remaining_qty > Decimal('0') and temp_opposing_book:
            if order.side == OrderSide.BUY:
                best_price, order_queue = temp_opposing_book.peekitem(0)
            else:
                best_price, order_queue = temp_opposing_book.peekitem(-1)
            
            if not price_check(order.price, best_price):
                return False
                
            for resting_order in order_queue:
                if remaining_qty <= Decimal('0'):
                    break
                    
                available_qty = resting_order.remaining_qty
                fill_qty = min(remaining_qty, available_qty)
                remaining_qty -= fill_qty
            
            if remaining_qty > Decimal('0'):
                if order.side == OrderSide.BUY:
                    temp_opposing_book.popitem(0)
                else:
                    temp_opposing_book.popitem(-1)
        
        return remaining_qty == Decimal('0')
    
    def _generate_trade(self, maker_order: Order, taker_order: Order, 
                       price: Decimal, quantity: Decimal) -> Trade:
        """Create trade execution record"""
        self.trade_id_counter += 1
        trade_id = f"TRD-{int(datetime.now().timestamp())}-{self.trade_id_counter:06d}"
        
        trade = Trade(
            trade_id=trade_id,
            timestamp=datetime.utcnow(),
            symbol=maker_order.symbol,
            price=price,
            quantity=quantity,
            aggressor_side=taker_order.side,
            maker_order_id=maker_order.order_id,
            taker_order_id=taker_order.order_id
        )
        
        # Calculate fees if enabled
        maker_fee_info = self.fee_calculator.calculate_fees(
        price, quantity, is_maker=True,
        client_tier=getattr(maker_order, 'client_tier', 'default')
        )
        taker_fee_info = self.fee_calculator.calculate_fees(
            price, quantity, is_maker=False, 
            client_tier=getattr(taker_order, 'client_tier', 'default')
        )
    
        trade.maker_fee = maker_fee_info["fee_amount"]
        trade.taker_fee = taker_fee_info["fee_amount"]
            # This would use a fee schedule based on client tiers
        
        self.trade_history.append(trade)
        
        # Log to WAL if enabled
        if self.wal:
            self.wal.log_trade(trade)
            
        logger.info(f"Trade executed: {trade}")
        return trade
    
    def _handle_remaining_quantity(self, order: Order, trades: List[Trade]) -> dict:
        """Handle unfilled quantity based on order type"""
        print(f"DEBUG: OrderStatus type = {type(OrderStatus)}")
        print(f"DEBUG: OrderStatus.PARTIAL = {OrderStatus.PARTIAL}")
        order_book = self.order_books[order.symbol]
        
        if order.remaining_qty > Decimal('0'):
            if order.type == OrderType.MARKET:
                # Market orders eat through available liquidity
                if len(trades) == 0:
                    order.reject()
                else:
                    order.status = OrderStatus.PARTIAL
                    
            elif order.type == OrderType.IOC:
                # IOC: Cancel unfilled portion
                if len(trades) > 0:
                    order.status = OrderStatus.PARTIAL_FILL_CANCELLED
                else:
                    order.reject()
                    
            elif order.type == OrderType.FOK:
                # FOK: Should never have remaining quantity if we passed _can_fill_completely
                order.reject()
                # In real implementation, would rollback trades
                
            elif order.type == OrderType.LIMIT:
                # Limit: Place remaining on book
                order_book.add_order(order)
                order.status = OrderStatus.PARTIAL if trades else OrderStatus.OPEN
        else:
            order.status = OrderStatus.FILLED
        
        # Calculate average fill price
        avg_fill_price = Decimal('0')
        total_filled = Decimal('0')
        
        for trade in trades:
            total_filled += trade.quantity
            avg_fill_price += trade.price * trade.quantity
        
        if total_filled > Decimal('0'):
            avg_fill_price /= total_filled
         
        response = order.to_dict()
        response["avg_fill_price"] = str(avg_fill_price) if total_filled > Decimal('0') else None

        # response["original_quantity"] = str(order.quantity)
        # response["timestamp"] = order.timestamp.isoformat()

        print(f"DEBUG: Response created successfully: {response}")
        
        return response
    
    def submit_advanced_order(self, order_data: dict) -> dict:
        """Submit stop-loss, stop-limit, take-profit orders"""
        try:
            advanced_order = AdvancedOrder(
                order_id=order_data.get("order_id", f"ADV-{int(datetime.now().timestamp())}-{len(self.advanced_orders)}"),
                symbol=order_data["symbol"],
                side=order_data["side"],
                quantity=Decimal(str(order_data["quantity"])),
                order_type=AdvancedOrderType(order_data["order_type"]),
                trigger_price=Decimal(str(order_data["trigger_price"])),
                limit_price=Decimal(str(order_data["limit_price"])) if order_data.get("limit_price") else None,
                client_id=order_data.get("client_id")
            )
        
            # Store advanced order
            if advanced_order.symbol not in self.advanced_orders:
                self.advanced_orders[advanced_order.symbol] = []
            self.advanced_orders[advanced_order.symbol].append(advanced_order)
        
            return {
                "order_id": advanced_order.order_id,
                "status": "pending",
                "order_type": advanced_order.order_type.value,
                "symbol": advanced_order.symbol,
                "side": advanced_order.side,
                "quantity": str(advanced_order.quantity),
                "trigger_price": str(advanced_order.trigger_price),
                "limit_price": str(advanced_order.limit_price) if advanced_order.limit_price else None
            }
        
        except Exception as e:
            return {"error": str(e), "status": "rejected"}

    def check_advanced_orders(self, symbol: str, current_price: Decimal):
        """Check and trigger advanced orders based on current price"""
        if symbol not in self.advanced_orders:
            return
    
        triggered_orders = []
        remaining_orders = []
    
        for order in self.advanced_orders[symbol]:
            if order.check_trigger(current_price):
                # Convert to regular order and submit
                regular_order = order.to_limit_order()
                result = self.submit_order(regular_order)
                triggered_orders.append(order.order_id)
            else:
                remaining_orders.append(order)
    
        self.advanced_orders[symbol] = remaining_orders
        return triggered_orders
    
    def _broadcast_updates(self, symbol: str, trades: List[Trade]) -> None:
        """Broadcast updates via WebSocket"""
        if self.websocket_manager:
            # Broadcast trades
            for trade in trades:
                self.websocket_manager.broadcast_trade(trade)
        
            # Broadcast order book update
            order_book = self.order_books[symbol]
            self.websocket_manager.broadcast_orderbook(symbol, order_book.get_depth())
            
            # Broadcast BBO update
            self.websocket_manager.broadcast_bbo(symbol, order_book.get_bbo())
    
    def cancel_order(self, order_id: str) -> dict:
        """Cancel an existing order"""
        for order_book in self.order_books.values():
            order = order_book.get_order(order_id)
            if order:
                if order.status in [OrderStatus.OPEN, OrderStatus.PARTIAL]:
                    removed_order = order_book.remove_order(order_id)
                    if removed_order:
                        removed_order.cancel()
                        
                        # Broadcast updates
                        self._broadcast_updates(removed_order.symbol, [])
                        
                        response = removed_order.to_dict()
                        response["cancelled_quantity"] = str(removed_order.remaining_qty)
                        return response
                else:
                    raise ValueError(f"Cannot cancel order in {order.status.value} state")
        
        raise ValueError(f"Order {order_id} not found")
    
    def get_orderbook(self, symbol: str, depth: int = 10) -> dict:
        """Get order book snapshot"""
        if symbol not in self.order_books:
            raise ValueError(f"Symbol {symbol} not found")
        
        order_book = self.order_books[symbol]
        depth_data = order_book.get_depth(depth)
        bbo = order_book.get_bbo()
        
        return {
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "bids": depth_data["bids"],
            "asks": depth_data["asks"],
            "bbo": bbo
        }
    
    def get_order(self, order_id: str) -> Optional[dict]:
        """Get order status"""
        for order_book in self.order_books.values():
            order = order_book.get_order(order_id)
            if order:
                return order.to_dict()
        return None
    
    def get_health(self) -> dict:
        """Get system health metrics"""
        uptime = (datetime.utcnow() - self.metrics["start_time"]).total_seconds()
        
        return {
            "status": "healthy",
            "uptime_seconds": uptime,
            "orders_processed": self.metrics["orders_processed"],
            "trades_executed": self.metrics["trades_executed"],
            "total_volume": str(self.metrics["total_volume"]),
            "active_symbols": list(self.order_books.keys()),
            "active_orders": sum(len(ob.orders) for ob in self.order_books.values()),
            "timestamp": datetime.utcnow().isoformat()
        }