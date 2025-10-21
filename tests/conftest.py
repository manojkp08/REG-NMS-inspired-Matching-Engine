import pytest
from src.engine.core.matching_engine import MatchingEngine

@pytest.fixture
def matching_engine():
    """Provide a fresh matching engine for each test"""
    return MatchingEngine()

@pytest.fixture
def populated_engine(matching_engine):
    """Provide engine with some initial orders"""
    # Add some buy orders
    matching_engine.submit_order({
        "symbol": "BTC-USDT", "order_type": "limit", "side": "buy",
        "quantity": "2.0", "price": "49900"
    })
    
    # Add some sell orders  
    matching_engine.submit_order({
        "symbol": "BTC-USDT", "order_type": "limit", "side": "sell",
        "quantity": "1.5", "price": "50100"
    })
    
    return matching_engine