import pytest
from src.engine.core.matching_engine import MatchingEngine

class TestOrderTypes:
    
    @pytest.fixture
    def engine(self):
        return MatchingEngine()
    
    def test_market_order_execution(self, engine):
        """Test market order executes at best available price"""
        # Setup order book
        engine.submit_order({
            "symbol": "BTC-USDT", "order_type": "limit", "side": "sell",
            "quantity": "1.0", "price": "50000"
        })
        engine.submit_order({
            "symbol": "BTC-USDT", "order_type": "limit", "side": "sell", 
            "quantity": "1.0", "price": "50100"
        })
        
        # Market buy
        result = engine.submit_order({
            "symbol": "BTC-USDT", "order_type": "market", "side": "buy",
            "quantity": "1.5"
        })
        
        assert result["status"] == "filled"
        assert result["filled_quantity"] == "1.5"
        # Should execute at best available prices
    
    def test_ioc_behavior(self, engine):
        """Test IOC fills what it can immediately, cancels rest"""
        engine.submit_order({
            "symbol": "BTC-USDT", "order_type": "limit", "side": "sell",
            "quantity": "2.0", "price": "50000"
        })
        
        # IOC for more than available
        result = engine.submit_order({
            "symbol": "BTC-USDT", "order_type": "ioc", "side": "buy",
            "quantity": "3.0", "price": "50000"
        })
        
        assert result["status"] == "partial_fill_cancelled"
        assert result["filled_quantity"] == "2.0"
        assert result["remaining_quantity"] == "0"  # Rest cancelled
    
    def test_fok_success(self, engine):
        """Test FOK executes when fully fillable"""
        engine.submit_order({
            "symbol": "BTC-USDT", "order_type": "limit", "side": "sell",
            "quantity": "2.0", "price": "50000"
        })
        
        result = engine.submit_order({
            "symbol": "BTC-USDT", "order_type": "fok", "side": "buy",
            "quantity": "2.0", "price": "50000"
        })
        
        assert result["status"] == "filled"
        assert result["filled_quantity"] == "2.0"
    
    def test_fok_rejection(self, engine):
        """Test FOK rejects when not fully fillable"""
        engine.submit_order({
            "symbol": "BTC-USDT", "order_type": "limit", "side": "sell",
            "quantity": "1.0", "price": "50000"
        })
        
        result = engine.submit_order({
            "symbol": "BTC-USDT", "order_type": "fok", "side": "buy", 
            "quantity": "2.0", "price": "50000"
        })
        
        assert result["status"] == "rejected"
        assert result["filled_quantity"] == "0"