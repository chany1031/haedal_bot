from flask import Flask
import threading
import os
import time
import logging
from datetime import datetime
from trading_engine import TradingEngine
from telegram_bot import TelegramBot

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_bot_loop():
    print("\n🚀 ETH Futures Trading Signal System")
    print("=" * 50)

    trading_engine = TradingEngine()

    # Initialize Telegram bot
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    telegram_bot = TelegramBot(token, chat_id) if token and chat_id else None

    if telegram_bot and telegram_bot.test_connection():
        print("✅ Telegram bot connected successfully")
        telegram_bot.send_message("🤖 Trading system started - monitoring ETH/USDT signals")
    else:
        print("⚠️ Telegram bot not connected or credentials missing")
        telegram_bot = None

    last_signal = None
    signal_count = 0

    print("\n📊 Starting market monitoring...")
    print("Press Ctrl+C to stop\n")

    while True:
        try:
            df = trading_engine.fetch_candles(interval='5m', limit=100)

            if df is None or df.empty:
                logger.warning("No candle data fetched")
                time.sleep(30)
                continue

            df = trading_engine.calculate_indicators(df)
            if df is None or len(df) < 2:
                logger.warning("Not enough valid data after indicator calculation")
                time.sleep(30)
                continue

            signal = trading_engine.generate_signal(df)
            if signal is None:
                signal = 'HOLD'

            current_price = df.iloc[-1]['close']
            market_summary = trading_engine.get_market_summary(df)
            timestamp = datetime.now().strftime("%H:%M:%S")

            print(f"[{timestamp}] ETH: ${current_price:.2f} | Signal: {signal}")

            if signal != 'HOLD' and signal != last_signal:
                signal_count += 1
                last_signal = signal

                entry, stop_loss, take_profit = trading_engine.suggest_trade_params(df, signal)
                if not all([entry, stop_loss, take_profit]):
                    continue

                risk = abs(entry - stop_loss)
                reward = abs(take_profit - entry)
                rr_ratio = round(reward / risk, 2) if risk > 0 else 0

                print("\n" + "="*50)
                print(f"🎯 TRADING SIGNAL #{signal_count} DETECTED!")
                print("="*50)
                print(f"Signal: {signal}")
                print(f"Entry Price: ${entry:.2f}")
                print(f"Stop Loss: ${stop_loss:.2f}")
                print(f"Take Profit: ${take_profit:.2f}")
                print(f"Risk/Reward: {rr_ratio}:1")
                if market_summary:
                    print(f"RSI: {market_summary['rsi']:.1f}")
                    print(f"EMA 20: ${market_summary['ema_20']:.2f}")
                    print(f"EMA 50: ${market_summary['ema_50']:.2f}")
                print("="*50 + "\n")

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

                    print("📱 Telegram alert sent successfully" if success else "❌ Failed to send Telegram alert")

            elif last_signal and signal == 'HOLD':
                last_signal = None
                print(f"[{timestamp}] Signal ended - back to monitoring")

        except Exception as e:
            logger.error(f"Error in trading loop: {e}")
            print(f"❌ Error: {e}")

        time.sleep(30)

@app.route('/')
def home():
    return "ETH Trading Bot is running!"

if __name__ == "__main__":
    t = threading.Thread(target=run_bot_loop)
    t.daemon = True
    t.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
