const WebSocket = require('ws');

// Choose which feed to connect to
const FEED_TYPE = 'trades'; // Options: 'orderbook', 'trades', 'bbo'
const ws = new WebSocket(`ws://localhost:8080/ws/${FEED_TYPE}`);

ws.on('open', () => {
    console.log(`✅ Connected to ${FEED_TYPE} feed`);

    // Send ping every 30 seconds to keep connection alive
    setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
            console.log('📤 sent ping');
        }
    }, 30000);
});

ws.on('message', (data) => {
    const message = data.toString();

    // Handle plain text pong responses
    if (message === 'pong') {
        console.log('✅ Received pong');
        return;
    }

    // Parse JSON messages
    try {
        const parsed = JSON.parse(message);

        // Handle different message types
        switch (parsed.type) {
            case 'subscribed':
                console.log(`✅ Successfully subscribed to ${parsed.channel} at ${parsed.timestamp}`);
                break;

            case 'orderbook_update':
                console.log(`\n📊 ORDERBOOK UPDATE: ${parsed.symbol}`);
                console.log(`   Timestamp: ${parsed.timestamp}`);
                console.log(`   Bids: ${parsed.bids.length} levels`);
                console.log(`   Asks: ${parsed.asks.length} levels`);
                if (parsed.bids.length > 0) {
                    console.log(`   Best Bid: ${parsed.bids[0][0]} (${parsed.bids[0][1]})`);
                }
                if (parsed.asks.length > 0) {
                    console.log(`   Best Ask: ${parsed.asks[0][0]} (${parsed.asks[0][1]})`);
                }
                break;

            case 'trade':
                console.log(`\n🎯 TRADE: ${parsed.quantity} ${parsed.symbol.split('/')[0]} @ $${parsed.price}`);
                console.log(`   Trade ID: ${parsed.trade_id}`);
                console.log(`   Side: ${parsed.aggressor_side}`);
                console.log(`   Fees: Maker ${parsed.maker_fee} / Taker ${parsed.taker_fee} ${parsed.fee_currency}`);
                console.log(`   Timestamp: ${parsed.timestamp}`);
                break;

            case 'bbo_update':
                const spread = parsed.spread ? `Spread: $${parsed.spread}` : 'No spread';
                console.log(`\n📈 BBO UPDATE: ${parsed.symbol}`);
                console.log(`   Bid: $${parsed.best_bid} (${parsed.best_bid_qty})`);
                console.log(`   Ask: $${parsed.best_ask} (${parsed.best_ask_qty})`);
                console.log(`   ${spread}`);
                console.log(`   Timestamp: ${parsed.timestamp}`);
                break;

            default:
                console.log('❓ Unknown message type:', parsed.type);
                console.log(JSON.stringify(parsed, null, 2));
        }
    } catch (error) {
        console.error('❌ Parse error:', error.message);
        console.log('Raw message:', message);
    }
});

ws.on('error', (error) => {
    console.error('❌ WebSocket error:', error.message);
});

ws.on('close', () => {
    console.log('🔌 Disconnected from WebSocket server');
});

// Handle graceful shutdown
process.on('SIGINT', () => {
    console.log('\n👋 Closing connection...');
    ws.close();
    process.exit(0);
});