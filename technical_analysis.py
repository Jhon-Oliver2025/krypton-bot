import pandas as pd
import numpy as np
import ta
import requests
from datetime import datetime, timedelta
import time
import json
import os

class TechnicalAnalysis:
    def __init__(self):
        self.futures_api = "https://fapi.binance.com/fapi/v1"
        self.timeframes = ['4h']
        self.futures_pairs = []
        self.signals_file = 'signals_history.csv'
        self._update_futures_pairs()

    def _update_futures_pairs(self):
        try:
            response = requests.get(f"{self.futures_api}/exchangeInfo")
            if response.status_code == 200:
                data = response.json()
                self.futures_pairs = [
                    f"{symbol['symbol']}" for symbol in data['symbols']
                    if symbol['symbol'].endswith('USDT') 
                    and symbol['status'] == 'TRADING'
                    and symbol['contractType'] == 'PERPETUAL'
                ]
                print(f"Pares futuros atualizados: {len(self.futures_pairs)}")
                print("Exemplos de pares:", self.futures_pairs[:5])
        except Exception as e:
            print(f"Erro na atualização dos pares: {e}")
            self.futures_pairs = []

    def get_klines(self, symbol, timeframe, retries=3):
        for attempt in range(retries):
            try:
                url = f"{self.futures_api}/klines"
                params = {
                    "symbol": symbol,
                    "interval": timeframe,
                    "limit": 100
                }
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 
                                                   'close_time', 'quote_volume', 'trades', 'taker_buy_volume',
                                                   'taker_buy_quote_volume', 'ignore'])
                    
                    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
                    df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    
                    return df
                else:
                    print(f"Erro na API: {response.status_code}")
                    time.sleep(2)
            except Exception as e:
                print(f"Tentativa {attempt + 1}/{retries} falhou: {e}")
                if attempt < retries - 1:
                    time.sleep(2)
                else:
                    print(f"Erro ao obter dados de {symbol} após {retries} tentativas")
                    return None
        return None

    def calculate_supertrend(self, df, period=10, multiplier=2.0):
        atr = ta.volatility.AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=period)
        df['atr'] = atr.average_true_range()
        
        df['pivot'] = (df['high'].rolling(window=period).max() + df['low'].rolling(window=period).min()) / 2
        df['upper_band'] = df['pivot'] + multiplier * df['atr']
        df['lower_band'] = df['pivot'] - multiplier * df['atr']
        
        df['trend'] = 0
        df['super_trend'] = 0.0
        
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['upper_band'].iloc[i-1]:
                df.loc[df.index[i], 'trend'] = 1
            elif df['close'].iloc[i] < df['lower_band'].iloc[i-1]:
                df.loc[df.index[i], 'trend'] = -1
            else:
                df.loc[df.index[i], 'trend'] = df['trend'].iloc[i-1]
                
            if df['trend'].iloc[i] == 1:
                df.loc[df.index[i], 'super_trend'] = df['lower_band'].iloc[i]
            else:
                df.loc[df.index[i], 'super_trend'] = df['upper_band'].iloc[i]
        
        return df

    def check_signal(self, df):
        if len(df) < 2:
            return None
            
        # Calcular RSI
        rsi = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        
        # Calcular MACD
        macd = ta.trend.MACD(df['close'])
        macd_line = macd.macd()
        signal_line = macd.macd_signal()
        
        # Dados básicos
        last_close = df["close"].iloc[-1]
        last_open = df["open"].iloc[-1]
        last_high = df["high"].iloc[-1]
        last_low = df["low"].iloc[-1]
        last_super_trend = df["super_trend"].iloc[-1]
        last_trend = df["trend"].iloc[-1]
        
        # Volume
        current_volume = df["volume"].iloc[-1]
        prev_volume = df["volume"].iloc[-2]
        avg_volume = df['volume'].rolling(window=20).mean().iloc[-1]
        
        # Análise de tendência
        trend_strength = sum(1 for i in range(-20, 0) if df['close'].iloc[i] > df['close'].iloc[i-1]) / 20
        
        # Sistema de Pontuação
        score = 0
        signal_type = None
        
        # Verificar condições para LONG
        if last_close > last_open and last_trend == 1:
            signal_type = "LONG"
            
            # SuperTrend alinhado (2 pontos)
            if last_low <= last_super_trend or last_high >= last_super_trend:
                score += 2
                
            # Volume crescente (1 ponto)
            if current_volume > prev_volume * 1.2 and current_volume > avg_volume:
                score += 1
                
            # RSI em zona ideal (1 ponto)
            if 40 < rsi.iloc[-1] < 70:
                score += 1
                
            # MACD confirmando (1 ponto)
            if macd_line.iloc[-1] > signal_line.iloc[-1]:
                score += 1
                
            # Tendência forte (2 pontos)
            if trend_strength > 0.6:
                score += 2
                
        # Verificar condições para SHORT
        elif last_close < last_open and last_trend == -1:
            signal_type = "SHORT"
            
            # SuperTrend alinhado (2 pontos)
            if last_high >= last_super_trend or last_low <= last_super_trend:
                score += 2
                
            # Volume crescente (1 ponto)
            if current_volume > prev_volume * 1.2 and current_volume > avg_volume:
                score += 1
                
            # RSI em zona ideal (1 ponto)
            if 30 < rsi.iloc[-1] < 60:
                score += 1
                
            # MACD confirmando (1 ponto)
            if macd_line.iloc[-1] < signal_line.iloc[-1]:
                score += 1
                
            # Tendência forte (2 pontos)
            if trend_strength < 0.4:
                score += 2
                
        # Retornar sinal apenas se atingir pontuação mínima de 6
        if score >= 6 and signal_type:
            print(f"\nPontuação do sinal: {score}/7")
            print(f"RSI: {rsi.iloc[-1]:.2f}")
            print(f"Força da tendência: {trend_strength:.2f}")
            return signal_type
            
        return None

    def check_signal_result(self, signal_data):
        """Verifica o resultado do sinal após 24 horas"""
        if datetime.now() >= signal_data['target_exit_time']:
            try:
                df = self.get_klines(signal_data['symbol'], '4h', retries=3)
                if df is not None:
                    current_price = df['close'].iloc[-1]
                    entry_price = signal_data['entry_price']
                    
                    # Calcula a variação percentual
                    if signal_data['type'] == "LONG":
                        variation = ((current_price - entry_price) / entry_price) * 100
                    else:  # SHORT
                        variation = ((entry_price - current_price) / entry_price) * 100
                    
                    # Atualiza o signal_data
                    signal_data['exit_price'] = current_price
                    signal_data['variation'] = variation
                    
                    # Calcula o resultado com investimento base
                    base_investment = 1000  # $1000 base
                    leverage = 50  # 50x
                    result = base_investment * (variation * leverage / 100)
                    
                    print(f"\nResultado após 24 horas:")
                    print(f"Par: {signal_data['symbol']}")
                    print(f"Tipo: {signal_data['type']}")
                    print(f"Preço entrada: {entry_price:.8f}")
                    print(f"Preço saída: {current_price:.8f}")
                    print(f"Variação: {variation:.2f}%")
                    print(f"Resultado ($1000 base): ${result:.2f}")
                    
                    return signal_data
                    
            except Exception as e:
                print(f"Erro ao verificar resultado: {e}")
                
        return signal_data

    def scan_market(self):
        print("\nIniciando varredura do mercado...")
        signals = []
        
        for symbol in self.futures_pairs:
            try:
                df = self.get_klines(symbol, '4h')
                if df is None or len(df) < 20:
                    continue
                    
                df = self.calculate_supertrend(df)
                signal = self.check_signal(df)
                
                if signal:
                    entry_time = datetime.now()
                    signal_data = {
                        'symbol': symbol,
                        'type': signal,
                        'entry_price': df['close'].iloc[-1],
                        'entry_time': entry_time,
                        'target_exit_time': entry_time + timedelta(hours=24),
                        'exit_price': None,
                        'variation': None,
                        'result': None,
                        'timeframe': '4h',
                        'status': 'OPEN'
                    }
                    
                    self.save_signal(signal_data)
                    signals.append(signal_data)
                    
                    print(f"\n🔔 Sinal encontrado!")
                    print(f"Par: {symbol}")
                    print(f"Tipo: {signal}")
                    print(f"Preço Entrada: {signal_data['entry_price']:.8f}")
                    print(f"Hora Entrada: {entry_time}")
                    print(f"Hora Saída Prevista: {signal_data['target_exit_time']}")
                    print("-" * 50)
                    
            except Exception as e:
                print(f"Erro em {symbol}: {e}")
                continue
        
        self.check_open_signals()
        return signals

    def save_signal(self, signal_data):
        """Salva o sinal no arquivo CSV"""
        if not os.path.exists(self.signals_file):
            with open(self.signals_file, 'w') as f:
                f.write("symbol,type,entry_price,entry_time,target_exit_time,exit_price,variation,result,timeframe,status\n")
        
        with open(self.signals_file, 'a') as f:
            f.write(f"{signal_data['symbol']},{signal_data['type']},{signal_data['entry_price']},{signal_data['entry_time']},"
                   f"{signal_data['target_exit_time']},{signal_data['exit_price']},{signal_data['variation']},"
                   f"{signal_data['result']},{signal_data['timeframe']},{signal_data['status']}\n")

    def check_open_signals(self):
        """Verifica resultados dos sinais abertos após 24h"""
        if not os.path.exists(self.signals_file):
            return
        
        signals_df = pd.read_csv(self.signals_file)
        open_signals = signals_df[signals_df['status'] == 'OPEN']
        
        for _, signal in open_signals.iterrows():
            target_exit_time = pd.to_datetime(signal['target_exit_time'])
            
            if datetime.now() >= target_exit_time:
                try:
                    df = self.get_klines(signal['symbol'], '4h')
                    if df is not None:
                        current_price = df['close'].iloc[-1]
                        entry_price = signal['entry_price']
                        
                        # Calcula variação
                        if signal['type'] == "LONG":
                            variation = ((current_price - entry_price) / entry_price) * 100
                        else:
                            variation = ((entry_price - current_price) / entry_price) * 100
                        
                        # Calcula resultado
                        base_investment = 1000
                        leverage = 50
                        result = base_investment * (variation * leverage / 100)
                        
                        # Atualiza o registro
                        signals_df.loc[signals_df['entry_time'] == signal['entry_time'], 'exit_price'] = current_price
                        signals_df.loc[signals_df['entry_time'] == signal['entry_time'], 'variation'] = variation
                        signals_df.loc[signals_df['entry_time'] == signal['entry_time'], 'result'] = result
                        signals_df.loc[signals_df['entry_time'] == signal['entry_time'], 'status'] = 'CLOSED'
                        
                        print(f"\nResultado após 24 horas:")
                        print(f"Par: {signal['symbol']}")
                        print(f"Tipo: {signal['type']}")
                        print(f"Preço entrada: {entry_price:.8f}")
                        print(f"Preço saída: {current_price:.8f}")
                        print(f"Variação: {variation:.2f}%")
                        print(f"Resultado ($1000 base): ${result:.2f}")
                        print("-" * 50)
                        
                except Exception as e:
                    print(f"Erro ao verificar resultado de {signal['symbol']}: {e}")
        
        signals_df.to_csv(self.signals_file, index=False)

    def monitor_pairs(self):
        return self.scan_market()