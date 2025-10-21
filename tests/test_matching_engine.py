import pytest
from decimal import Decimal
from src.engine.core.matching_engine import MatchingEngine
from src.engine.core.order import Order, OrderSide, OrderType

class TestMatchingEngine:
    
    @pytest.fixture
    def engine(self):
        return MatchingEngine()
    
    def test_simple_match(self, engine):
        """Basic buy-sell match at same price"""
        # Place limit sell
        sell_result = engine.submit_order({
            "symbol": "BTC-USDT",
            "order_type": "limit", 
            "side": "sell",
            "quantity": "1.0",
            "price": "50000"
        })
        
        # Place limit buy (should match)
        buy_result = engine.submit_order({
            "symbol": "BTC-USDT", 
            "order_type": "limit",
            "side": "buy",
            "quantity": "1.0", 
            "price": "50000"
        })
        
        assert buy_result["status"] == "filled"
        assert sell_result["status"] == "filled"
    
    def test_price_priority(self, engine):
        """Higher bid gets filled first"""
        # Place two sell orders at different prices
        engine.submit_order({
            "symbol": "BTC-USDT",
            "order_type": "limit",
            "side": "sell", 
            "quantity": "1.0",
            "price": "50100"  # Worse price
        })
        
        engine.submit_order({
            "symbol": "BTC-USDT",
            "order_type": "limit",
            "side": "sell",
            "quantity": "1.0", 
            "price": "50000"  # Better price
        })
        
        # Market buy should match with better price
        result = engine.submit_order({
            "symbol": "BTC-USDT",
            "order_type": "market", 
            "side": "buy",
            "quantity": "1.0"
        })
        
        assert result["avg_fill_price"] == "50000"
    
    def test_ioc_partial_fill(self, engine):
        """IOC order partial fill and cancel"""
        engine.submit_order({
            "symbol": "BTC-USDT",
            "order_type": "limit",
            "side": "sell",
            "quantity": "1.0",
            "price": "50000"
        })
        
        # IOC buy for more than available
        result = engine.submit_order({
            "symbol": "BTC-USDT",
            "order_type": "ioc",
            "side": "buy", 
            "quantity": "2.0",
            "price": "50000"
        })
        
        assert result["status"] == "partial_fill_cancelled"
        assert result["filled_quantity"] == "1.0"
        assert result["remaining_quantity"] == "0"
    
    def test_fok_rejection(self, engine):
        """FOK order rejects when not fully fillable"""
        engine.submit_order({
            "symbol": "BTC-USDT", 
            "order_type": "limit",
            "side": "sell",
            "quantity": "1.0",
            "price": "50000"
        })
        
        # FOK buy for more than available
        result = engine.submit_order({
            "symbol": "BTC-USDT",
            "order_type": "fok", 
            "side": "buy",
            "quantity": "2.0",
            "price": "50000"
        })
        
        assert result["status"] == "rejected"
        assert result["filled_quantity"] == "0"
    
    def test_market_order_empty_book(self, engine):
        """Market order on empty book is rejected"""
        result = engine.submit_order({
            "symbol": "BTC-USDT",
            "order_type": "market",
            "side": "buy", 
            "quantity": "1.0"
        })
        
        assert result["status"] == "rejected"
    
    def test_cancel_order(self, engine):
        """Cancel open order"""
        order = engine.submit_order({
            "symbol": "BTC-USDT",
            "order_type": "limit", 
            "side": "buy",
            "quantity": "1.0",
            "price": "50000"
        })
        
        cancel_result = engine.cancel_order(order["order_id"])
        
        assert cancel_result["status"] == "cancelled"
        assert cancel_result["cancelled_quantity"] == "1.0"