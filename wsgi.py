from app import app, start_monitoring, background_monitor, analyzer, db, notifier
import threading
import time

print("=== Iniciando KryptoN Trading Bot ===")

def setup_inicial():
    try:
        print("\nConfigurando sistema...")
        # Configura apenas BTC para teste inicial
        analyzer.futures_pairs = [
            'BTCUSDT'  # Apenas BTC por enquanto
        ]
        print(f"Par configurado: {analyzer.futures_pairs[0]}")
        
        # Configura apenas timeframe de 4H
        analyzer.timeframes = ['4h']
        print(f"Timeframe configurado: 4H")
        
        # Configurações ultra conservadoras
        analyzer.period = '3'  # Reduz período ao mínimo
        analyzer.retry_delay = 600  # 10 minutos entre chamadas
        analyzer.max_retries = 1  # Apenas uma tentativa
        analyzer.timeout = 120  # 2 minutos de timeout
        analyzer.keep_alive = True  # Mantém conexão ativa
        print("Configurações de API ajustadas para modo ultra conservador")
        
        # Força limpeza de memória
        import gc
        gc.collect()
        
        return True
    except Exception as e:
        print(f"Erro na configuração inicial: {e}")
        return False

def verificar_configuracoes():
    try:
        # Executa setup inicial
        if not setup_inicial():
            return False
        
        # Testa conexão com API
        print("\nTestando conexão com API...")
        test_pair = analyzer.futures_pairs[0]
        test_data = analyzer.get_klines(test_pair, '4h')  # Removido o parâmetro limit
        if test_data is not None:
            print("Conexão com API OK")
        
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