# 1. Install dependencies
pip install -r requirements.txt

# 2. Start REST API (Terminal 1)
python -m src.engine.api.rest_server

# 3. Start WebSocket (Terminal 2)
python -m src.engine.api.websocket_feeds

# 4. Run tests
pytest tests/