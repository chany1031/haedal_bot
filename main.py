#!/usr/bin/env python3
"""
Cryptocurrency Trading Signal System - Main Entry Point
Real-time ETH/USDT futures technical analysis with Telegram alerts
"""

import os
import time
import logging
from datetime import datetime
from trading_engine import TradingEngine
from telegram_bot import TelegramBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main trading system loop"""
    print("🚀 ETH Futures Trading Signal System")
    print("=" * 50)
    
    # Initialize trading engine with default parameters
    trading_engine = TradingEngine(
        ema_short=20,
        ema_long=50,
        rsi_period=14,
        atr_period=14,
        macd_fast=12,
        macd_slow=26,
        macd_signal=9
    )
    
    # Initialize Telegram bot
    telegram_bot = None
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if token and chat_id:
        telegram_bot = TelegramBot(token, chat_id)
        if telegram_bot.test_connection():
            print("✅ Telegram bot connected successfully")
            telegram_bot.send_message("🤖 Trading system started - monitoring ETH/USDT signals")
        else:
            print("❌ Telegram bot connection failed")
            telegram_bot = None
    else:
        print("⚠️ Telegram credentials not found - alerts disabled")
    
    # Trading loop
    last_signal = None
    signal_count = 0
    
    print("\n📊 Starting market monitoring...")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            try:
                # Fetch market data
                df = trading_engine.fetch_candles(interval='5m', limit=100)
                
                if df is not None and not df.empty:
                    # Calculate technical indicators
                    df = trading_engine.calculate_indicators(df)
                    
                    if df is not None:
                        # Generate trading signal
                        signal = trading_engine.generate_signal(df)
                        current_price = df.iloc[-1]['close']
                        
                        # Get market summary
                        market_summary = trading_engine.get_market_summary(df)
                        
                        # Display current status
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"[{timestamp}] ETH: ${current_price:.2f} | Signal: {signal}")
                        
                        # Check for new signal
                        if signal != 'HOLD' and signal != last_signal:
                            signal_count += 1
                            last_signal = signal
                            
                            # Get trade parameters
                            entry, stop_loss, take_profit = trading_engine.suggest_trade_params(df, signal)
                            
                            if entry and stop_loss and take_profit:
                                # Calculate risk/reward
                                if signal == 'LONG':
                                    risk = entry - stop_loss
                                    reward = take_profit - entry
                                else:
                                    risk = stop_loss - entry
                                    reward = entry - take_profit
                                
                                rr_ratio = reward / risk if risk > 0 else 0
                                
                                # Print signal details
                                print("\n" + "="*50)
                                print(f"🎯 TRADING SIGNAL #{signal_count} DETECTED!")
                                print("="*50)
                                print(f"Signal: {signal}")
                                print(f"Entry Price: ${entry:.2f}")
                                print(f"Stop Loss: ${stop_loss:.2f}")
                                print(f"Take Profit: ${take_profit:.2f}")
                                print(f"Risk/Reward: {rr_ratio:.2f}:1")
                                
                                if market_summary:
                                    print(f"RSI: {market_summary['rsi']:.1f}")
                                    print(f"EMA 20: ${market_summary['ema_20']:.2f}")
                                    print(f"EMA 50: ${market_summary['ema_50']:.2f}")
                                
                                print("="*50 + "\n")
                                
                                # Send Telegram alert
                                if telegram_bot:
                                    additional_info = {
                                        'EMA 20': market_summary['ema_20'],
                                        'EMA 50': market_summary['ema_50'],
                                        'RSI': market_summary['rsi'],
                                        'MACD': market_summary['macd'],
                                        'OBV': 'Bullish' if signal == 'LONG' else 'Bearish'
                                    } if market_summary else None
                                    
                                    success = telegram_bot.send_signal_alert(
                                        signal=signal,
                                        entry=entry,
                                        stop_loss=stop_loss,
                                        take_profit=take_profit,
                                        rr_ratio=rr_ratio,
                                        additional_info=additional_info
                                    )
                                    
                                    if success:
                                        print("📱 Telegram alert sent successfully")
                                    else:
                                        print("❌ Failed to send Telegram alert")
                        
                        elif last_signal and signal == 'HOLD':
                            # Signal ended
                            last_signal = None
                            print(f"[{timestamp}] Signal ended - back to monitoring")
                
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Failed to fetch market data")
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                print(f"❌ Error: {e}")
            
            # Wait before next check
            time.sleep(30)  # Check every 30 seconds
            
    except KeyboardInterrupt:
        print("\n\n🛑 Trading system stopped by user")
        if telegram_bot:
            telegram_bot.send_message("🛑 Trading system stopped")
        print("Thank you for using the ETH Trading Signal System!")

if __name__ == "__main__":
    if __name__ == '__main__':
    t = threading.Thread(target=run_bot_loop)
    t.daemon = True
    t.start()
    
    # Render가 할당한 포트를 받아서 Flask에 전달
    import os
    port = int(os.environ.get("PORT", 10000))  # default는 10000
    app.run(host='0.0.0.0', port=port)
