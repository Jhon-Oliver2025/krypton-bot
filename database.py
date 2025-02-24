import sqlite3
from datetime import datetime, timedelta
import threading

class SignalDatabase:
    def __init__(self):
        self._local = threading.local()
        self.connect()
        self.create_tables()

    def connect(self):
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect('signals.db', check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row

    def get_connection(self):
        self.connect()
        return self._local.conn

    def create_tables(self):
        conn = self.get_connection()
        conn.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                type TEXT NOT NULL,
                price FLOAT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                entry_price FLOAT NOT NULL,
                max_price FLOAT DEFAULT NULL,
                min_price FLOAT DEFAULT NULL,
                best_result FLOAT DEFAULT NULL,
                monitoring_end_date TEXT NOT NULL,
                completed BOOLEAN DEFAULT FALSE,
                days_active INTEGER DEFAULT 0,
                is_historical BOOLEAN DEFAULT FALSE
            )
        ''')
        conn.commit()

    def add_signal(self, signal_data):
        conn = self.get_connection()
        cursor = conn.cursor()
        monitoring_end = datetime.now() + timedelta(days=7)
        
        try:
            if isinstance(signal_data['timestamp'], datetime):
                timestamp_str = signal_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            else:
                timestamp_str = signal_data['timestamp']
            
            monitoring_end_str = monitoring_end.strftime('%Y-%m-%d %H:%M:%S')
            
            # Primeiro, vamos verificar se o sinal já existe
            cursor.execute('''
                SELECT COUNT(*) FROM signals 
                WHERE symbol = ? AND type = ? AND timestamp = ?
            ''', (signal_data['symbol'], signal_data['type'], timestamp_str))
            
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO signals (
                        symbol, type, price, timeframe, timestamp, 
                        entry_price, monitoring_end_date, is_historical
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    signal_data['symbol'],
                    signal_data['type'],
                    signal_data['price'],
                    signal_data['timeframe'],
                    timestamp_str,
                    signal_data['price'],
                    monitoring_end_str,
                    False
                ))
                conn.commit()
                print(f"Novo sinal salvo com sucesso: {signal_data}")
            else:
                print("Sinal duplicado ignorado")
                
        except Exception as e:
            print(f"Erro ao salvar sinal: {e}")
            import traceback
            traceback.print_exc()
            conn.rollback()

    def get_recent_signals(self, hours=24):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            time_limit = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                SELECT symbol, type, price, timeframe, timestamp
                FROM signals
                WHERE timestamp >= ?
                AND is_historical = 0
                ORDER BY timestamp DESC
            ''', (time_limit,))
            
            columns = ['symbol', 'type', 'price', 'timeframe', 'timestamp']
            results = cursor.fetchall()
            
            signals = []
            for row in results:
                signal = {}
                for i, column in enumerate(columns):
                    signal[column] = row[i]
                signals.append(signal)
            
            print(f"Total de sinais encontrados: {len(signals)}")
            print(f"Sinais recuperados: {signals}")
            return signals
            
        except Exception as e:
            print(f"Erro ao buscar sinais recentes: {e}")
            import traceback
            traceback.print_exc()
            return []
    def get_historical_signals(self):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT symbol, type, price, timeframe, timestamp, days_active
                FROM signals
                WHERE is_historical = 1
                ORDER BY datetime(timestamp) DESC
            ''')
            
            signals = [dict(row) for row in cursor]
            return signals
            
        except Exception as e:
            print(f"Erro ao buscar histórico: {e}")
            return []

    def get_statistics(self):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    AVG(best_result) as avg_result,
                    MAX(best_result) as best_result,
                    SUM(CASE WHEN best_result > 0 THEN 1 ELSE 0 END) as wins
                FROM signals
                WHERE completed = TRUE
            ''')
            
            result = cursor.fetchone()
            total = result['total'] if result['total'] else 0
            wins = result['wins'] if result['wins'] else 0
            win_rate = (wins / total * 100) if total > 0 else 0
            
            return {
                'win_rate': win_rate,
                'avg_result': result['avg_result'] or 0,
                'best_result': result['best_result'] or 0
            }
        except Exception as e:
            print(f"Erro ao buscar estatísticas: {e}")
            return {
                'win_rate': 0,
                'avg_result': 0,
                'best_result': 0
            }