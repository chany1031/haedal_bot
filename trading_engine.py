import requests
import pandas as pd
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradingEngine:
    """Cryptocurrency trading signal engine with technical analysis"""
    
    def __init__(self, ema_short=20, ema_long=50, rsi_period=14, atr_period=14, 
                 macd_fast=12, macd_slow=26, macd_signal=9):
        self.ema_short = ema_short
        self.ema_long = ema_long
        self.rsi_period = rsi_period
        self.atr_period = atr_period
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        
    def fetch_candles(self, interval='5m', limit=100):
        """Fetch candlestick data from Gate.io API"""
        try:
            url = f'https://api.gateio.ws/api/v4/futures/usdt/candlesticks'
            params = {
                'contract': 'ETH_USDT',
                'interval': interval,
                'limit': limit
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                logger.error("No data received from API")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(data, columns=['time', 'volume', 'close', 'high', 'low', 'open'])
            
            # Convert data types
            df['time'] = pd.to_datetime(df['time'], unit='s')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])
            
            # Rename volume column for consistency
            df = df.rename(columns={'volume': 'base_vol'})
            df['quote_vol'] = df['base_vol'] * df['close']  # Approximate quote volume
            
            # Sort by time
            df = df.sort_values('time').reset_index(drop=True)
            
            logger.info(f"Successfully fetched {len(df)} candles")
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching candles: {e}")
            return None
    
    def calculate_indicators(self, df):
    """Calculate technical indicators with proper NaN handling"""
    try:
        if df is None or df.empty:
            logger.warning("DataFrame is None or empty")
            return None

        # 충분한 데이터 길이 확인
        min_required = max(self.ema_long, self.macd_slow, self.rsi_period, self.atr_period)
        if len(df) < min_required:
            logger.warning(f"Insufficient data rows ({len(df)}); minimum required: {min_required}")
            return None

        # EMA
        df[f'EMA{self.ema_short}'] = EMAIndicator(
            df['close'], window=self.ema_short
        ).ema_indicator()

        df[f'EMA{self.ema_long}'] = EMAIndicator(
            df['close'], window=self.ema_long
        ).ema_indicator()

        # Alias for compatibility
        df['SMA20'] = df[f'EMA{self.ema_short}']
        df['SMA50'] = df[f'EMA{self.ema_long}']

        # MACD
        macd = MACD(
            df['close'],
            window_fast=self.macd_fast,
            window_slow=self.macd_slow,
            window_sign=self.macd_signal
        )
        df['MACD'] = macd.macd()
        df['MACD_signal'] = macd.macd_signal()
        df['MACD_histogram'] = macd.macd_diff()

        # RSI
        df['RSI'] = RSIIndicator(
            df['close'], window=self.rsi_period
        ).rsi()

        # ATR
        df['ATR'] = AverageTrueRange(
            df['high'], df['low'], df['close'], window=self.atr_period
        ).average_true_range()

        # OBV
        df['OBV'] = OnBalanceVolumeIndicator(
            df['close'], df['base_vol']
        ).on_balance_volume()

        # 필요한 컬럼 정의
        required_cols = [
            f'EMA{self.ema_short}', f'EMA{self.ema_long}',
            'MACD', 'MACD_signal', 'MACD_histogram',
            'RSI', 'ATR', 'OBV'
        ]

        # NaN 제거
        initial_len = len(df)
        df.dropna(subset=required_cols, inplace=True)
        final_len = len(df)
        if final_len < initial_len:
            logger.warning(f"Dropped {initial_len - final_len} rows with NaN in indicators")

        # 인덱스 재정렬
        df = df.reset_index(drop=True)

        logger.info("Technical indicators calculated and cleaned successfully")
        return df

    except Exception as e:
        logger.error(f"Error calculating indicators: {e}")
        return None

    
    def generate_signal(self, df):
        """Generate trading signals based on technical analysis"""
        try:
            if df is None or len(df) < 2:
                return 'HOLD'
            
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Check for NaN values
            required_cols = ['SMA20', 'SMA50', 'MACD', 'MACD_signal', 'RSI', 'OBV']
            if any(pd.isna(latest[col]) for col in required_cols):
                logger.warning("Missing indicator values, returning HOLD")
                return 'HOLD'
            
            # SMA crossover signals
            cross_long = (prev['SMA20'] <= prev['SMA50']) and (latest['SMA20'] > latest['SMA50'])
            cross_short = (prev['SMA20'] >= prev['SMA50']) and (latest['SMA20'] < latest['SMA50'])
            
            # MACD signals
            macd_bullish = latest['MACD'] > latest['MACD_signal']
            macd_bearish = latest['MACD'] < latest['MACD_signal']
            
            # RSI conditions
            rsi_not_overbought = latest['RSI'] < 70
            rsi_not_oversold = latest['RSI'] > 30
            
            # OBV trend confirmation
            obv_bullish = latest['OBV'] > prev['OBV']
            obv_bearish = latest['OBV'] < prev['OBV']
            
            # Generate signals with OBV confirmation
            if cross_long and macd_bullish and rsi_not_overbought and obv_bullish:
                logger.info("LONG signal generated with OBV confirmation")
                return 'LONG'
            elif cross_short and macd_bearish and rsi_not_oversold and obv_bearish:
                logger.info("SHORT signal generated with OBV confirmation")
                return 'SHORT'
            else:
                return 'HOLD'
                
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return 'HOLD'
    
    def suggest_trade_params(self, df, position):
        """Suggest entry, stop loss, and take profit levels"""
        try:
            if df is None or position == 'HOLD':
                return None, None, None
            
            latest = df.iloc[-1]
            entry = latest['close']
            atr = latest['ATR']
            
            if pd.isna(atr):
                logger.warning("ATR value is NaN, using 1% of price as fallback")
                atr = entry * 0.01
            
            if position == 'LONG':
                stop_loss = entry - atr * 1.5
                take_profit = entry + (entry - stop_loss) * 2
            elif position == 'SHORT':
                stop_loss = entry + atr * 1.5
                take_profit = entry - (stop_loss - entry) * 2
            else:
                return None, None, None
            
            return round(entry, 2), round(stop_loss, 2), round(take_profit, 2)
            
        except Exception as e:
            logger.error(f"Error calculating trade parameters: {e}")
            return None, None, None
    
    def get_market_summary(self, df):
        """Get current market summary"""
        try:
            if df is None or df.empty:
                return None
            
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            price_change = latest['close'] - prev['close']
            price_change_pct = (price_change / prev['close']) * 100
            
            summary = {
                'current_price': latest['close'],
                'price_change': price_change,
                'price_change_pct': price_change_pct,
                'volume': latest['base_vol'],
                'rsi': latest['RSI'],
                'macd': latest['MACD'],
                'macd_signal': latest['MACD_signal'],
                'ema_20': latest['SMA20'],
                'ema_50': latest['SMA50'],
                'atr': latest['ATR'],
                'obv': latest['OBV']
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting market summary: {e}")
            return None
