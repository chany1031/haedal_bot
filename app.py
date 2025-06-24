import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import os
from datetime import datetime, timedelta
from trading_engine import TradingEngine
from telegram_bot import TelegramBot

# Page configuration
st.set_page_config(
    page_title="Crypto Trading Signals",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'signal_history' not in st.session_state:
    st.session_state.signal_history = []
if 'last_update' not in st.session_state:
    st.session_state.last_update = None
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if 'telegram_configured' not in st.session_state:
    st.session_state.telegram_configured = False

def main():
    st.title("🚀 Cryptocurrency Trading Signal System")
    st.markdown("Real-time ETH Futures Technical Analysis & Trading Signals")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Telegram Bot Configuration
        st.subheader("Telegram Bot Settings")
        telegram_token = st.text_input(
            "Bot Token",
            value=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            type="password",
            help="Enter your Telegram bot token"
        )
        telegram_chat_id = st.text_input(
            "Chat ID",
            value=os.getenv("TELEGRAM_CHAT_ID", ""),
            help="Enter your Telegram chat ID"
        )
        
        if telegram_token and telegram_chat_id:
            st.session_state.telegram_configured = True
            st.success("✅ Telegram configured")
        else:
            st.session_state.telegram_configured = False
            st.warning("⚠️ Telegram not configured")
        
        st.divider()
        
        # Technical Analysis Parameters
        st.subheader("Technical Indicators")
        ema_short = st.slider("EMA Short Period", 10, 30, 20)
        ema_long = st.slider("EMA Long Period", 30, 100, 50)
        rsi_period = st.slider("RSI Period", 10, 20, 14)
        atr_period = st.slider("ATR Period", 10, 20, 14)
        macd_fast = st.slider("MACD Fast", 8, 15, 12)
        macd_slow = st.slider("MACD Slow", 20, 30, 26)
        macd_signal = st.slider("MACD Signal", 7, 12, 9)
        
        st.divider()
        
        # Data Settings
        st.subheader("Data Settings")
        interval = st.selectbox("Timeframe", ['1m', '5m', '15m', '30m', '1h'], index=1)
        limit = st.slider("Data Points", 50, 200, 100)
        
        st.divider()
        
        # Auto Refresh
        auto_refresh = st.checkbox("Auto Refresh (30s)", value=st.session_state.auto_refresh)
        st.session_state.auto_refresh = auto_refresh
        
        if st.button("🔄 Manual Refresh", use_container_width=True):
            st.rerun()
    
    # Initialize trading engine
    trading_engine = TradingEngine(
        ema_short=ema_short,
        ema_long=ema_long,
        rsi_period=rsi_period,
        atr_period=atr_period,
        macd_fast=macd_fast,
        macd_slow=macd_slow,
        macd_signal=macd_signal
    )
    
    # Initialize telegram bot
    telegram_bot = None
    if st.session_state.telegram_configured:
        telegram_bot = TelegramBot(telegram_token, telegram_chat_id)
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Fetch and display data
        with st.spinner("Fetching market data..."):
            try:
                df = trading_engine.fetch_candles(interval=interval, limit=limit)
                df = trading_engine.calculate_indicators(df)
                
                if df is not None and not df.empty:
                    st.session_state.last_update = datetime.now()
                    
                    # Generate trading signal
                    signal = trading_engine.generate_signal(df)
                    latest_price = df.iloc[-1]['close']
                    
                    # Display current market info
                    st.subheader(f"📊 ETH/USDT Futures - {interval} Timeframe")
                    
                    metric_cols = st.columns(4)
                    with metric_cols[0]:
                        price_change = ((df.iloc[-1]['close'] - df.iloc[-2]['close']) / df.iloc[-2]['close']) * 100
                        st.metric("Current Price", f"${latest_price:.2f}", f"{price_change:+.2f}%")
                    
                    with metric_cols[1]:
                        st.metric("Signal", signal, help="Current trading recommendation")
                    
                    with metric_cols[2]:
                        rsi_value = df.iloc[-1]['RSI']
                        rsi_status = "Overbought" if rsi_value > 70 else "Oversold" if rsi_value < 30 else "Neutral"
                        st.metric("RSI", f"{rsi_value:.1f}", rsi_status)
                    
                    with metric_cols[3]:
                        volume = df.iloc[-1]['base_vol']
                        st.metric("Volume", f"{volume:.0f}")
                    
                    # Create interactive chart
                    fig = create_trading_chart(df)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Trading recommendations
                    if signal != 'HOLD':
                        entry, stop_loss, take_profit = trading_engine.suggest_trade_params(df, signal)
                        
                        st.subheader(f"🎯 Trading Recommendation: {signal}")
                        
                        rec_cols = st.columns(3)
                        with rec_cols[0]:
                            st.metric("Entry Price", f"${entry:.2f}")
                        with rec_cols[1]:
                            st.metric("Stop Loss", f"${stop_loss:.2f}")
                        with rec_cols[2]:
                            st.metric("Take Profit", f"${take_profit:.2f}")
                        
                        # Risk/Reward calculation
                        if signal == 'LONG':
                            risk = entry - stop_loss
                            reward = take_profit - entry
                        else:
                            risk = stop_loss - entry
                            reward = entry - take_profit
                        
                        rr_ratio = reward / risk if risk > 0 else 0
                        st.info(f"Risk/Reward Ratio: {rr_ratio:.2f}:1")
                        
                        # Add to signal history
                        signal_data = {
                            'timestamp': datetime.now(),
                            'signal': signal,
                            'price': latest_price,
                            'entry': entry,
                            'stop_loss': stop_loss,
                            'take_profit': take_profit,
                            'rr_ratio': rr_ratio
                        }
                        
                        # Check if this is a new signal
                        if not st.session_state.signal_history or \
                           st.session_state.signal_history[-1]['signal'] != signal or \
                           abs(st.session_state.signal_history[-1]['price'] - latest_price) > latest_price * 0.01:
                            
                            st.session_state.signal_history.append(signal_data)
                            
                            # Send telegram notification
                            if telegram_bot:
                                message = (
                                    f"🟢 Trading Signal Detected 🟢\n"
                                    f"Signal: {signal}\n"
                                    f"Entry: ${entry:.2f}\n"
                                    f"Stop Loss: ${stop_loss:.2f}\n"
                                    f"Take Profit: ${take_profit:.2f}\n"
                                    f"R/R Ratio: {rr_ratio:.2f}:1"
                                )
                                telegram_bot.send_message(message)
                    
                else:
                    st.error("Failed to fetch market data. Please check your connection.")
                    
            except Exception as e:
                st.error(f"Error fetching data: {str(e)}")
    
    with col2:
        # Signal History
        st.subheader("📈 Signal History")
        
        if st.session_state.signal_history:
            for i, signal_data in enumerate(reversed(st.session_state.signal_history[-10:])):
                with st.container():
                    signal_color = "🟢" if signal_data['signal'] == 'LONG' else "🔴"
                    st.write(f"{signal_color} **{signal_data['signal']}**")
                    st.caption(f"{signal_data['timestamp'].strftime('%H:%M:%S')}")
                    st.caption(f"${signal_data['price']:.2f}")
                    if i < len(st.session_state.signal_history) - 1:
                        st.divider()
        else:
            st.info("No signals generated yet")
        
        # System Status
        st.subheader("🔧 System Status")
        if st.session_state.last_update:
            time_diff = datetime.now() - st.session_state.last_update
            st.success(f"✅ Data updated {time_diff.seconds}s ago")
        
        if st.session_state.telegram_configured:
            st.success("✅ Telegram alerts enabled")
        else:
            st.warning("⚠️ Telegram alerts disabled")
        
        if st.session_state.auto_refresh:
            st.success("🔄 Auto-refresh enabled")
        else:
            st.info("🔄 Auto-refresh disabled")
    
    # Auto refresh logic
    if st.session_state.auto_refresh:
        time.sleep(30)
        st.rerun()

def create_trading_chart(df):
    """Create an interactive trading chart with technical indicators"""
    
    # Create subplots
    fig = make_subplots(
        rows=5, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        subplot_titles=('Price & Exponential Moving Averages', 'MACD', 'RSI', 'Volume', 'OBV'),
        row_width=[0.2, 0.15, 0.15, 0.25, 0.25]
    )
    
    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=df['time'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name="Price"
        ),
        row=1, col=1
    )
    
    # Exponential Moving averages
    fig.add_trace(
        go.Scatter(
            x=df['time'],
            y=df['SMA20'],
            line=dict(color='orange', width=2),
            name='EMA 20'
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=df['time'],
            y=df['SMA50'],
            line=dict(color='blue', width=2),
            name='EMA 50'
        ),
        row=1, col=1
    )
    
    # MACD
    fig.add_trace(
        go.Scatter(
            x=df['time'],
            y=df['MACD'],
            line=dict(color='green', width=2),
            name='MACD'
        ),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=df['time'],
            y=df['MACD_signal'],
            line=dict(color='red', width=2),
            name='MACD Signal'
        ),
        row=2, col=1
    )
    
    # RSI
    fig.add_trace(
        go.Scatter(
            x=df['time'],
            y=df['RSI'],
            line=dict(color='purple', width=2),
            name='RSI'
        ),
        row=3, col=1
    )
    
    # RSI levels
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
    fig.add_hline(y=50, line_dash="dash", line_color="gray", row=3, col=1)
    
    # Volume
    fig.add_trace(
        go.Bar(
            x=df['time'],
            y=df['base_vol'],
            name='Volume',
            marker_color='lightblue'
        ),
        row=4, col=1
    )
    
    # OBV (On-Balance Volume)
    fig.add_trace(
        go.Scatter(
            x=df['time'],
            y=df['OBV'],
            line=dict(color='teal', width=2),
            name='OBV'
        ),
        row=5, col=1
    )
    
    # Update layout
    fig.update_layout(
        title="ETH/USDT Technical Analysis",
        xaxis_rangeslider_visible=False,
        height=1000,
        showlegend=True,
        hovermode='x unified'
    )
    
    # Update y-axis labels
    fig.update_yaxes(title_text="Price ($)", row=1, col=1)
    fig.update_yaxes(title_text="MACD", row=2, col=1)
    fig.update_yaxes(title_text="RSI", row=3, col=1, range=[0, 100])
    fig.update_yaxes(title_text="Volume", row=4, col=1)
    fig.update_yaxes(title_text="OBV", row=5, col=1)
    
    return fig

if __name__ == "__main__":
    main()
