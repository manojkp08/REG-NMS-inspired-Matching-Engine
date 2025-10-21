from enum import Enum

class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"

class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    IOC = "ioc"
    FOK = "fok"

class OrderStatus(str, Enum):
    PENDING = "pending"
    OPEN = "open"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    PARTIAL_FILL_CANCELLED = "partial_fill_cancelled"

# Default configuration
DEFAULT_SYMBOL = "BTC-USDT"
MAX_ORDER_QUANTITY = 1000000  # Prevent ridiculously large orders
MAX_PRICE = 1000000  # $1M max price