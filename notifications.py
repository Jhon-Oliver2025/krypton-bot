import requests
from datetime import datetime, timedelta

class TelegramNotifier:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"

    def send_signal(self, signal_data):
        try:
            is_long = signal_data['type'] == 'LONG'
            emoji = "🟢" if is_long else "🔴"
            direction = "para cima" if is_long else "para baixo"
            
            message = (
                f"{emoji} Ativo: {signal_data['symbol'].replace('.P', '')}\n"
                f"⏱ Candle: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
                f"🤖 KryptonBot confirmado {direction}"
            )
            
            url = f"{self.base_url}/sendMessage"
            params = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, params=params)
            if not response.ok:
                print(f"Erro ao enviar mensagem: {response.text}")
                
        except Exception as e:
            print(f"Erro ao enviar notificação: {e}")