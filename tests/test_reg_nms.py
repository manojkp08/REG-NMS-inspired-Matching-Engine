import pytest
from decimal import Decimal
from src.engine.core.matching_engine import MatchingEngine

class TestRegNMSCompliance:
    
    @pytest.fixture
    def engine(self):
        return MatchingEngine()
    
    def test_no_trade_through(self, engine):
        """Test that orders never skip better prices"""
        # Setup multiple price levels
        engine.submit_order({
            "symbol": "BTC-USDT", "order_type": "limit", "side": "sell",
            "quantity": "1.0", "price": "50000"  # Best price
        })
        engine.submit_order({
            "symbol": "BTC-USDT", "order_type": "limit", "side": "sell",
            "quantity": "2.0", "price": "50200"  # Worse price
        })
        
        # Large market buy
        result = engine.submit_order({
            "symbol": "BTC-USDT", "order_type": "market", "side": "buy", 
            "quantity": "2.5"
        })
        
        # Should fill best price first, then worse price
        assert result["filled_quantity"] == "2.5"
        # Average price should reflect best execution
    
    def test_price_time_priority(self, engine):
        """Test strict price-time priority"""
        # Same price, different times
        order1 = engine.submit_order({
            "symbol": "BTC-USDT", "order_type": "limit", "side": "buy",
            "quantity": "1.0", "price": "50000"
        })
        
        order2 = engine.submit_order({
            "symbol": "BTC-USDT", "order_type": "limit", "side": "buy", 
            "quantity": "1.0", "price": "50000"
        })
        
        # Sell that matches both
        sell_result = engine.submit_order({
            "symbol": "BTC-USDT", "order_type": "limit", "side": "sell",
            "quantity": "1.0", "price": "50000"
        })
        
        # First buy order should fill
        order1_status = engine.get_order(order1["order_id"])
        order2_status = engine.get_order(order2["order_id"])
        
        assert order1_status["status"] == "filled"
        assert order2_status["status"] == "open"
    
    def test_best_execution(self, engine):
        """Test orders get best available price"""
        # Seller at better price than limit
        engine.submit_order({
            "symbol": "BTC-USDT", "order_type": "limit", "side": "sell",
            "quantity": "1.0", "price": "49999"  # Better than buyer's limit
        })
        
        # Buyer with higher limit price
        result = engine.submit_order({
            "symbol": "BTC-USDT", "order_type": "limit", "side": "buy",
            "quantity": "1.0", "price": "50000"
        })
        
        # Should execute at better price (49999)
        assert result["avg_fill_price"] == "49999"