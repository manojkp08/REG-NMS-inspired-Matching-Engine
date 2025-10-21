from decimal import Decimal
from typing import Dict

class FeeCalculator:
    def __init__(self):
        self.fee_tiers = {
            "default": {
                "maker_fee": Decimal('0.001'),  # 0.1%
                "taker_fee": Decimal('0.002'),  # 0.2%
            },
            "vip": {
                "maker_fee": Decimal('0.0005'),  # 0.05%
                "taker_fee": Decimal('0.0015'),  # 0.15%
            }
        }
    
    def calculate_fees(self, price: Decimal, quantity: Decimal, 
                      is_maker: bool, client_tier: str = "default") -> Dict[str, Decimal]:
        """Calculate maker and taker fees for a trade"""
        tier = self.fee_tiers.get(client_tier, self.fee_tiers["default"])
        
        fee_rate = tier["maker_fee"] if is_maker else tier["taker_fee"]
        fee_amount = price * quantity * fee_rate
        
        return {
            "fee_rate": fee_rate,
            "fee_amount": fee_amount,
            "currency": "USDT"  # Assuming USDT denominated fees
        }