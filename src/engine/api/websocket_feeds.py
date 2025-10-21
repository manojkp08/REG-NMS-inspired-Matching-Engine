import asyncio
import websockets
import json
import logging
from typing import Set, Dict
from datetime import datetime

# Configure logging at module level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.subscribers: Dict[str, Set] = {
            'orderbook': set(),
            'trades': set(),
            'bbo': set()
        }
        self.server = None

    async def handler(self, websocket):
        """Handle WebSocket connections"""
        # Get path from websocket.request.path in newer versions
        path = websocket.request.path
        logger.info(f"New connection from {websocket.remote_address} on path: {path}")
        try:
            # Determine feed type from path
            if path == '/ws/orderbook':
                await self._handle_orderbook_feed(websocket)
            elif path == '/ws/trades':
                await self._handle_trade_feed(websocket)
            elif path == '/ws/bbo':
                await self._handle_bbo_feed(websocket)
            else:
                logger.warning(f"Invalid path requested: {path}")
                await websocket.close(1003, "Invalid feed type")
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection closed from {websocket.remote_address}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}", exc_info=True)
            await websocket.close(1011, "Internal server error")

    async def _handle_orderbook_feed(self, websocket):
        """Handle order book feed subscriptions"""
        self.subscribers['orderbook'].add(websocket)
        logger.info(f"Orderbook subscriber added. Total: {len(self.subscribers['orderbook'])}")
        try:
            # Send initial confirmation
            await websocket.send(json.dumps({
                "type": "subscribed",
                "channel": "orderbook",
                "timestamp": datetime.utcnow().isoformat()
            }))
            
            # Keep connection alive
            async for message in websocket:
                # Handle ping-pong or other client messages
                if message.strip() == "ping":
                    await websocket.send("pong")
                
        
                    
        finally:
            self.subscribers['orderbook'].discard(websocket)
            logger.info(f"Orderbook subscriber removed. Total: {len(self.subscribers['orderbook'])}")

    async def _handle_trade_feed(self, websocket):
        """Handle trade feed subscriptions"""
        self.subscribers['trades'].add(websocket)
        logger.info(f"Trade subscriber added. Total: {len(self.subscribers['trades'])}")
        try:
            await websocket.send(json.dumps({
                "type": "subscribed", 
                "channel": "trades",
                "timestamp": datetime.utcnow().isoformat()
            }))
            
            async for message in websocket:
                if message.strip() == "ping":
                    await websocket.send("pong")
                    
        finally:
            self.subscribers['trades'].discard(websocket)
            logger.info(f"Trade subscriber removed. Total: {len(self.subscribers['trades'])}")

    async def _handle_bbo_feed(self, websocket):
        """Handle BBO feed subscriptions"""
        self.subscribers['bbo'].add(websocket)
        logger.info(f"BBO subscriber added. Total: {len(self.subscribers['bbo'])}")
        try:
            await websocket.send(json.dumps({
                "type": "subscribed",
                "channel": "bbo", 
                "timestamp": datetime.utcnow().isoformat()
            }))
            
            async for message in websocket:
                if message.strip() == "ping":
                    await websocket.send("pong")
                    
        finally:
            self.subscribers['bbo'].discard(websocket)
            logger.info(f"BBO subscriber removed. Total: {len(self.subscribers['bbo'])}")

    async def broadcast_trade(self, trade):
        """Broadcast trade to all trade feed subscribers"""
        if not self.subscribers['trades']:
            return
            
        message = {
            "type": "trade",
            "timestamp": trade.timestamp.isoformat(),
            "symbol": trade.symbol,
            "trade_id": trade.trade_id,
            "price": str(trade.price),
            "quantity": str(trade.quantity),
            "aggressor_side": trade.aggressor_side,
            "maker_order_id": trade.maker_order_id,
            "taker_order_id": trade.taker_order_id,
            "maker_fee": str(trade.maker_fee),
            "taker_fee": str(trade.taker_fee),
            "fee_currency": "USDT"
        }
        
        message_json = json.dumps(message)
        disconnected = set()
        
        for websocket in self.subscribers['trades']:
            try:
                await websocket.send(message_json)
            except Exception as e:
                logger.error(f"Failed to send trade to subscriber: {e}")
                disconnected.add(websocket)
                
        # Remove disconnected clients
        self.subscribers['trades'] -= disconnected

    async def broadcast_orderbook(self, symbol, orderbook_data):
        """Broadcast order book update"""
        if not self.subscribers['orderbook']:
            return
            
        message = {
            "type": "orderbook_update",
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": symbol,
            "bids": orderbook_data["bids"],
            "asks": orderbook_data["asks"]
        }
        
        message_json = json.dumps(message)
        disconnected = set()
        
        for websocket in self.subscribers['orderbook']:
            try:
                await websocket.send(message_json)
            except Exception as e:
                logger.error(f"Failed to send orderbook to subscriber: {e}")
                disconnected.add(websocket)
                
        self.subscribers['orderbook'] -= disconnected

    async def broadcast_bbo(self, symbol, bbo_data):
        """Broadcast BBO update"""
        if not self.subscribers['bbo']:
            return
            
        message = {
            "type": "bbo_update",
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": symbol,
            "best_bid": str(bbo_data["best_bid"]) if bbo_data["best_bid"] else None,
            "best_bid_qty": str(bbo_data["best_bid_qty"]),
            "best_ask": str(bbo_data["best_ask"]) if bbo_data["best_ask"] else None,
            "best_ask_qty": str(bbo_data["best_ask_qty"]),
            "spread": str(bbo_data["spread"]) if bbo_data["spread"] else None
        }
        
        message_json = json.dumps(message)
        disconnected = set()
        
        for websocket in self.subscribers['bbo']:
            try:
                await websocket.send(message_json)
            except Exception as e:
                logger.error(f"Failed to send BBO to subscriber: {e}")
                disconnected.add(websocket)
                
        self.subscribers['bbo'] -= disconnected

    async def start_server(self, host="0.0.0.0", port=8080):
        """Start WebSocket server"""
        logger.info(f"Starting WebSocket server on {host}:{port}...")
        
        self.server = await websockets.serve(
            self.handler, host, port
        )
        
        logger.info("=" * 60)
        logger.info(f"✓ WebSocket server is running on ws://{host}:{port}")
        logger.info(f"  - Order Book Feed: ws://{host}:{port}/ws/orderbook")
        logger.info(f"  - Trade Feed:      ws://{host}:{port}/ws/trades")
        logger.info(f"  - BBO Feed:        ws://{host}:{port}/ws/bbo")
        logger.info("=" * 60)
        logger.info("Server is ready to accept connections. Press Ctrl+C to stop.")
        
        # Keep server running
        try:
            await asyncio.Future()
        except KeyboardInterrupt:
            logger.info("Shutting down WebSocket server...")

# Global WebSocket manager instance
ws_manager = WebSocketManager()

def start_websocket_server():
    """Start WebSocket server (blocking)"""
    try:
        asyncio.run(ws_manager.start_server())
    except KeyboardInterrupt:
        logger.info("WebSocket server stopped")

if __name__ == "__main__":
    start_websocket_server()