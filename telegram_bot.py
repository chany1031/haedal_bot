import requests
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramBot:
    """Telegram bot for sending trading alerts"""
    
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f'https://api.telegram.org/bot{token}'
        
    def send_message(self, text: str) -> bool:
        """Send a text message to the configured chat"""
        try:
            url = f'{self.base_url}/sendMessage'
            params = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': 'HTML'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('ok'):
                logger.info("Telegram message sent successfully")
                return True
            else:
                logger.error(f"Telegram API error: {result.get('description', 'Unknown error')}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error sending Telegram message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram message: {e}")
            return False
    
    def send_signal_alert(self, signal: str, entry: float, stop_loss: float, 
                         take_profit: float, rr_ratio: float, 
                         additional_info: Optional[dict] = None) -> bool:
        """Send a formatted trading signal alert"""
        
        signal_emoji = "🟢" if signal == "LONG" else "🔴"
        
        message = f"""
{signal_emoji} <b>Trading Signal Alert</b> {signal_emoji}

<b>Signal:</b> {signal}
<b>Entry Price:</b> ${entry:.2f}
<b>Stop Loss:</b> ${stop_loss:.2f}
<b>Take Profit:</b> ${take_profit:.2f}
<b>Risk/Reward:</b> {rr_ratio:.2f}:1
"""
        
        if additional_info:
            message += "\n<b>Additional Info:</b>\n"
            for key, value in additional_info.items():
                if isinstance(value, (int, float)):
                    message += f"• {key}: {value:.2f}\n"
                else:
                    message += f"• {key}: {value}\n"
        
        message += f"\n<i>Generated at: {self._get_current_time()}</i>"
        
        return self.send_message(message)
    
    def send_market_update(self, price: float, change_pct: float, 
                          volume: float, rsi: float) -> bool:
        """Send a market update message"""
        
        change_emoji = "📈" if change_pct > 0 else "📉"
        
        message = f"""
📊 <b>Market Update</b>

{change_emoji} <b>ETH/USDT:</b> ${price:.2f} ({change_pct:+.2f}%)
📊 <b>Volume:</b> {volume:.0f}
📈 <b>RSI:</b> {rsi:.1f}

<i>Updated at: {self._get_current_time()}</i>
"""
        
        return self.send_message(message)
    
    def test_connection(self) -> bool:
        """Test the Telegram bot connection"""
        try:
            url = f'{self.base_url}/getMe'
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('ok'):
                bot_info = result.get('result', {})
                logger.info(f"Telegram bot connection successful. Bot: {bot_info.get('first_name', 'Unknown')}")
                return True
            else:
                logger.error(f"Telegram bot test failed: {result.get('description', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Error testing Telegram connection: {e}")
            return False
    
    def _get_current_time(self) -> str:
        """Get current time formatted for messages"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    @staticmethod
    def validate_config(token: str, chat_id: str) -> tuple[bool, str]:
        """Validate Telegram bot configuration"""
        if not token or not token.strip():
            return False, "Bot token is required"
        
        if not chat_id or not chat_id.strip():
            return False, "Chat ID is required"
        
        # Basic token format validation
        if not token.startswith(('bot', '')) or ':' not in token:
            return False, "Invalid bot token format"
        
        # Basic chat ID validation (should be numeric for private chats)
        try:
            int(chat_id)
        except ValueError:
            # Could be a channel username starting with @
            if not chat_id.startswith('@'):
                return False, "Invalid chat ID format"
        
        return True, "Configuration is valid"
