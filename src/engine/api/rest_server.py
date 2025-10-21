from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from decimal import Decimal

from .schemas import OrderRequest, OrderResponse, CancelResponse, OrderBookResponse, HealthResponse
from ..core.matching_engine import MatchingEngine
from .schemas import AdvancedOrderRequest, AdvancedOrderResponse

# Configure logging at module level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GoQuant Matching Engine",
    description="High-performance cryptocurrency matching engine",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global matching engine instance
matching_engine = MatchingEngine()

@app.on_event("startup")
async def startup_event():
    """Log startup information"""
    logger.info("=" * 60)
    logger.info("✓ GoQuant Matching Engine API is starting...")
    logger.info(f"  - Title: {app.title}")
    logger.info(f"  - Version: {app.version}")
    logger.info("  - Matching Engine initialized")
    logger.info("=" * 60)

@app.post("/api/v1/orders", response_model=OrderResponse)
async def submit_order(order_request: OrderRequest):
    """Submit a new order to the matching engine"""
    try:
        order_data = order_request.dict()
        result = matching_engine.submit_order(order_data)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
            
        return result
        
    except Exception as e:
        logger.error(f"Error submitting order: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/v1/orders/{order_id}", response_model=CancelResponse)
async def cancel_order(order_id: str):
    """Cancel an existing order"""
    try:
        result = matching_engine.cancel_order(order_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error cancelling order: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/orders/{order_id}")
async def get_order(order_id: str):
    """Get order status"""
    try:
        order = matching_engine.get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return order
    except Exception as e:
        logger.error(f"Error getting order: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/orderbook/{symbol}", response_model=OrderBookResponse)
async def get_orderbook(symbol: str, depth: int = 10):
    """Get current order book snapshot"""
    try:
        result = matching_engine.get_orderbook(symbol, depth)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting orderbook: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """System health check"""
    try:
        return matching_engine.get_health()
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="System unhealthy")

@app.get("/")
async def root():
    return {"message": "GoQuant Matching Engine API", "version": "1.0.0"}

@app.post("/api/v1/advanced-orders", response_model=AdvancedOrderResponse)
async def submit_advanced_order(order_request: AdvancedOrderRequest):
    """Submit stop-loss, stop-limit, or take-profit order"""
    try:
        order_data = order_request.dict()
        result = matching_engine.submit_advanced_order(order_data)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
            
        return result
        
    except Exception as e:
        logger.error(f"Error submitting advanced order: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/performance")
async def get_performance_metrics():
    """Get performance metrics"""
    try:
        # You need to import or initialize perf_tracker
        # from ..core.performance import perf_tracker
        # return perf_tracker.get_summary()
        
        # For now, return a placeholder
        return {
            "status": "performance tracking not yet implemented",
            "note": "Import perf_tracker to enable this endpoint"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def start_server():
    """Start the REST API server"""
    logger.info("Starting REST API server...")
    logger.info("Server will be available at: http://0.0.0.0:8000")
    logger.info("API docs will be available at: http://0.0.0.0:8000/docs")
    logger.info("Press Ctrl+C to stop the server")
    
    uvicorn.run(
        "src.engine.api.rest_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Set to True for development
        log_level="info"
    )

if __name__ == "__main__":
    start_server()