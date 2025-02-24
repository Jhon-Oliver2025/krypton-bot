from app import app, start_monitoring, background_monitor, analyzer, db, notifier
import threading
import time

print("=== Iniciando KryptoN Trading Bot ===")

def setup_inicial():
    try:
        print("\nConfigurando sistema...")
        # Configura pares diretamente
        analyzer.futures_pairs = [
            'BTCUSDT.P', 'ETHUSDT.P', 'BNBUSDT.P', 'XRPUSDT.P', 'ADAUSDT.P',
            'DOGEUSDT.P', 'MATICUSDT.P', 'SOLUSDT.P', 'DOTUSDT.P', 'LTCUSDT.P'
        ]
        print(f"Pares configurados: {len(analyzer.futures_pairs)}")
        print(f"Lista de pares: {analyzer.futures_pairs}")
        
        # Configura timeframes
        analyzer.timeframes = ['4h', '1h', '15m']
        print(f"Timeframes configurados: {analyzer.timeframes}")
        
        # Configura período
        analyzer.period = '1000'
        print("Período configurado:", analyzer.period)
        
        return True
    except Exception as e:
        print(f"Erro na configuração inicial: {e}")
        return False

def verificar_configuracoes():
    try:
        # Executa setup inicial
        if not setup_inicial():
            return False
        
        # Verifica Telegram
        print("\nVerificando configuração do Telegram...")
        if hasattr(notifier, 'telegram_token'):
            print("Token do Telegram configurado")
        else:
            print("AVISO: Token do Telegram não encontrado")
        
        # Verifica banco de dados
        print("\nVerificando banco de dados...")
        sinais = db.get_recent_signals(hours=24)
        print(f"Banco de dados OK - {len(sinais)} sinais encontrados")
        
        return True
    except Exception as e:
        print(f"Erro na verificação: {e}")
        return False

def iniciar_monitoramento_com_retry():
    tentativas = 0
    while tentativas < 3:
        try:
            print("\nIniciando sistema de monitoramento...")
            if verificar_configuracoes():
                monitor_thread = threading.Thread(target=background_monitor, daemon=True)
                monitor_thread.start()
                print("Thread de monitoramento iniciada com sucesso")
                return True
        except Exception as e:
            tentativas += 1
            print(f"Tentativa {tentativas}: Erro ao iniciar monitoramento: {e}")
            print("Aguardando 10 segundos antes de tentar novamente...")
            time.sleep(10)
    
    print("Falha ao iniciar monitoramento após 3 tentativas")
    return False

# Inicia o monitoramento
if iniciar_monitoramento_com_retry():
    print("Sistema iniciado com sucesso!")
else:
    print("ATENÇÃO: Sistema iniciado sem monitoramento!")

# Expõe o servidor para o gunicorn
server = app.server