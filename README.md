# Crypto Trading Signal System

## Overview

This is a real-time cryptocurrency trading signal system built with Streamlit that provides technical analysis and trading signals for ETH/USDT futures. The application fetches live market data from Gate.io API, performs technical analysis using various indicators, and can send trading alerts via Telegram bot integration.

## System Architecture

The application follows a modular Python architecture with clear separation of concerns:

- **Frontend**: Streamlit web application providing an interactive dashboard
- **Trading Engine**: Core technical analysis engine for signal generation
- **Telegram Integration**: Bot service for sending trading alerts
- **Data Source**: Gate.io API for real-time market data

## Key Components

### 1. Main Application (app.py)
- **Purpose**: Streamlit frontend interface
- **Features**: 
  - Real-time dashboard with trading signals
  - Configuration interface for Telegram bot settings
  - Signal history tracking
  - Auto-refresh capabilities
- **Architecture Decision**: Chose Streamlit for rapid prototyping and easy deployment, allowing non-technical users to interact with the trading system through a web interface

### 2. Trading Engine (trading_engine.py)
- **Purpose**: Core technical analysis and signal generation
- **Technical Indicators**:
  - Exponential Moving Averages (EMA 20/50)
  - MACD (12, 26, 9)
  - RSI (14 period)
  - Average True Range (ATR)
  - On-Balance Volume (OBV)
- **Architecture Decision**: Separated trading logic into its own module for reusability and easier testing. Uses the `ta` library for reliable technical indicator calculations. Updated to use EMA for more responsive signal generation. OBV added for volume confirmation of price trends.

### 3. Telegram Bot (telegram_bot.py)
- **Purpose**: Alert notification system
- **Features**:
  - Formatted trading signal messages
  - Error handling and logging
  - HTML message formatting support
- **Architecture Decision**: Implemented as a separate service to enable notifications without requiring users to monitor the dashboard constantly

### 4. Configuration Management
- **Environment Variables**: Telegram bot credentials stored securely
- **Streamlit Config**: Custom theme and server settings in `.streamlit/config.toml`
- **Dependencies**: Managed via `pyproject.toml` with uv package manager

## Data Flow

1. **Data Acquisition**: Gate.io API provides real-time ETH/USDT futures candlestick data
2. **Technical Analysis**: Trading engine processes price data and calculates technical indicators
3. **Signal Generation**: Algorithm analyzes indicator combinations to generate buy/sell signals
4. **Visualization**: Streamlit dashboard displays charts and current market conditions
5. **Alert Distribution**: Telegram bot sends formatted trading signals to configured chat

## External Dependencies

### APIs and Services
- **Gate.io API**: Primary data source for cryptocurrency market data
  - Endpoint: `https://api.gateio.ws/api/v4/futures/usdt/candlesticks`
  - Rate limits and error handling implemented
- **Telegram Bot API**: For sending trading alerts
  - Requires bot token and chat ID configuration

### Python Libraries
- **Streamlit**: Web application framework
- **Pandas**: Data manipulation and analysis
- **Plotly**: Interactive charting and visualization
- **TA-Lib**: Technical analysis indicators
- **Requests**: HTTP client for API calls

## Deployment Strategy

### Replit Configuration
- **Runtime**: Python 3.11 with Nix package management
- **Deployment Target**: Autoscale deployment for handling variable traffic
- **Port Configuration**: Streamlit runs on port 5000
- **Workflow**: Automated setup installs dependencies (plotly, ta) and starts the application

### Environment Setup
- **Package Manager**: UV for fast Python package management
- **Dependencies**: Locked versions in `uv.lock` for reproducible builds
- **Configuration**: Environment variables for sensitive data (Telegram credentials)

### Pros and Cons of Architecture Choices

**Streamlit Frontend**
- Pros: Rapid development, built-in widgets, automatic reactivity
- Cons: Limited customization compared to full web frameworks
- Rationale: Chosen for speed of development and ease of deployment

**Gate.io API Integration**
- Pros: Free access, reliable futures data, good documentation
- Cons: Dependency on external service, potential rate limits
- Rationale: Provides the specific ETH futures data needed for the trading strategy

**Modular Python Structure**
- Pros: Testable components, reusable code, clear separation of concerns
- Cons: Slightly more complex than monolithic approach
- Rationale: Enables easier maintenance and future feature additions

## Changelog

```
Changelog:
- June 24, 2025. Initial setup
- June 24, 2025. Updated trading indicators from SMA to EMA for more responsive signals
- June 24, 2025. Added On-Balance Volume (OBV) indicator for volume trend confirmation
```

## User Preferences

```
Preferred communication style: Simple, everyday language.
```
