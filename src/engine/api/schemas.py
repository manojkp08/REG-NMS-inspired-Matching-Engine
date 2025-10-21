from pydantic import BaseModel, Field, validator
from typing import Optional
from decimal import Decimal

class OrderRequest(BaseModel):
    symbol: str = Field(..., example="BTC-USDT")
    order_type: str = Field(..., example="limit")
    side: str = Field(..., example="buy")
    quantity: str = Field(..., example="1.5")
    price: Optional[str] = Field(None, example="50000.00")
    client_id: Optional[str] = Field(None, example="client_123")

    @validator('order_type')
    def validate_order_type(cls, v):
        valid_types = ['market', 'limit', 'ioc', 'fok']
        if v.lower() not in valid_types:
            raise ValueError(f'Order type must be one of: {valid_types}')
        return v.lower()

    @validator('side')
    def validate_side(cls, v):
        if v.lower() not in ['buy', 'sell']:
            raise ValueError('Side must be "buy" or "sell"')
        return v.lower()

    @validator('quantity')
    def validate_quantity(cls, v):
        try:
            qty = Decimal(v)
            if qty <= 0:
                raise ValueError('Quantity must be positive')
            return v
        except:
            raise ValueError('Quantity must be a valid decimal number')

    @validator('price')
    def validate_price(cls, v, values):
        if 'order_type' in values and values['order_type'] != 'market' and v is None:
            raise ValueError('Price is required for limit orders')
        
        if v is not None:
            try:
                price = Decimal(v)
                if price <= 0:
                    raise ValueError('Price must be positive')
                return v
            except:
                raise ValueError('Price must be a valid decimal number')
        return v

class OrderResponse(BaseModel):
    order_id: str
    status: str
    symbol: str
    order_type: str
    side: str
    original_quantity: str
    filled_quantity: str
    remaining_quantity: str
    avg_fill_price: Optional[str]
    timestamp: str

class CancelResponse(BaseModel):
    order_id: str
    status: str
    filled_quantity: str
    cancelled_quantity: str
    timestamp: str

class OrderBookResponse(BaseModel):
    symbol: str
    timestamp: str
    bids: list
    asks: list
    bbo: dict

class HealthResponse(BaseModel):
    status: str
    uptime_seconds: float
    orders_processed: int
    trades_executed: int
    active_symbols: list
    timestamp: str


class AdvancedOrderRequest(BaseModel):
    symbol: str = Field(..., example="BTC-USDT")
    order_type: str = Field(..., example="stop_loss")  # stop_loss, stop_limit, take_profit
    side: str = Field(..., example="buy")
    quantity: str = Field(..., example="1.0")
    trigger_price: str = Field(..., example="49000.00")
    limit_price: Optional[str] = Field(None, example="48900.00")  # Required for stop_limit
    client_id: Optional[str] = Field(None, example="client_123")

    @validator('order_type')
    def validate_advanced_order_type(cls, v):
        valid_types = ['stop_loss', 'stop_limit', 'take_profit']
        if v.lower() not in valid_types:
            raise ValueError(f'Advanced order type must be one of: {valid_types}')
        return v.lower()

class AdvancedOrderResponse(BaseModel):
    order_id: str
    status: str
    order_type: str
    symbol: str
    side: str
    quantity: str
    trigger_price: str
    limit_price: Optional[str]