from app import app, start_monitoring, background_monitor, analyzer, db, notifier
import threading
import time

print("=== Iniciando KryptoN Trading Bot ===")

def setup_inicial():
    try:
        print("\nConfigurando sistema...")
        # Configura apenas BTC em spot
        analyzer.futures_pairs = [
            'BTCUSDT'  # Mercado spot
        ]
        print(f"Par configurado: {analyzer.futures_pairs[0]}")
        
        # Configura apenas timeframe de 4H
        analyzer.timeframes = ['4h']
        print(f"Timeframe configurado: 4H")
        
        # Configurações para API pública
        analyzer.period = '1'  # Apenas 1 vela
        analyzer.retry_delay = 7200  # 2 horas entre chamadas
        analyzer.max_retries = 1  # Sem retry
        analyzer.timeout = 5  # Timeout mínimo
        analyzer.use_spot = True  # Força mercado spot
        analyzer.api_weight = 1  # Peso mínimo
        analyzer.use_public_api = True  # Força uso da API pública
        analyzer.region = 'asia'  # Tenta região da Ásia
        print("Configurações ajustadas para API pública")
        
        # Adiciona verificação de IP
        import requests
        try:
            ip = requests.get('https://api.ipify.org?format=json', timeout=5).json()
            print(f"IP do servidor: {ip['ip']}")
        except:
            print("Não foi possível verificar o IP")
        
        return True
    except Exception as e:
        print(f"Erro na configuração inicial: {e}")
        return False

# Configura porta para o gunicorn
app.server.config.update({
    'PORT': 10000,
    'host': '0.0.0.0',
    'workers': 1,
    'timeout': 120
})
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