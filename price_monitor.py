import sqlite3
from datetime import datetime, timedelta
import requests

class PriceMonitor:
    def __init__(self):
        self.conn = sqlite3.connect('signals.db')
        self.futures_api = "https://fapi.binance.com/fapi/v1"
        self.leverage = 50  # Alavancagem fixa em 50x

    def get_current_price(self, symbol):
        try:
            url = f"{self.futures_api}/ticker/price"
            response = requests.get(url, params={'symbol': symbol.replace('.P', '')})
            if response.status_code == 200:
                return float(response.json()['price'])
            return None
        except Exception as e:
            print(f"Erro ao obter preço: {e}")
            return None

    def update_signal_results(self):
        active_signals = self.conn.execute('''
            SELECT id, symbol, type, entry_price, max_price, min_price
            FROM signals 
            WHERE completed = FALSE AND monitoring_end_date > datetime('now')
        ''').fetchall()

        for signal in active_signals:
            current_price = self.get_current_price(signal[1])
            if not current_price:
                continue

            max_price = max(signal[4] or current_price, current_price)
            min_price = min(signal[5] or current_price, current_price)
            
            # Calcula melhor resultado baseado no tipo de operação
            if signal[2] == 'LONG':
                best_result = ((max_price - signal[3]) / signal[3]) * 100 * self.leverage
            else:
                best_result = ((signal[3] - min_price) / signal[3]) * 100 * self.leverage

            self.conn.execute('''
                UPDATE signals 
                SET max_price = ?, min_price = ?, best_result = ?
                WHERE id = ?
            ''', (max_price, min_price, best_result, signal[0]))
            
        self.conn.commit()

    def close_expired_signals(self):
        self.conn.execute('''
            UPDATE signals 
            SET completed = TRUE 
            WHERE completed = FALSE 
            AND monitoring_end_date <= datetime('now')
        ''')
        self.conn.commit()