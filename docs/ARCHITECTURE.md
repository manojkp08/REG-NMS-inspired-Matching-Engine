# GoQuant Matching Engine - Architecture

## System Overview

A high-performance cryptocurrency matching engine implementing price-time priority and REG NMS compliance.

## Core Components

### 1. Order Book
- **Data Structure**: SortedDict + Deque
- **Performance**: O(log n) inserts, O(1) BBO access
- **Fairness**: Price-time priority within price levels

### 2. Matching Engine
- **Algorithm**: Price-time priority matching
- **Order Types**: Market, Limit, IOC, FOK
- **Compliance**: No trade-throughs, best execution

### 3. API Layer
- **REST API**: Order submission, cancellation, queries
- **WebSocket**: Real-time market data feeds
- **Validation**: Pydantic models for all requests

## Key Features

1. Price-time priority matching  
2. All major order types  
3. Real-time WebSocket feeds  
4. REG NMS compliance  
5. High performance (>1000 orders/sec)  
6. Comprehensive testing  