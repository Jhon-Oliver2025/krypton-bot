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
        
        # Configurações para API pública
        analyzer.period = '1'  # Apenas 1 vela
        analyzer.retry_delay = 7200  # 2 horas entre chamadas
        analyzer.max_retries = 1  # Sem retry
        analyzer.timeout = 5  # Timeout mínimo
        analyzer.use_spot = True  # Força mercado spot
        analyzer.api_weight = 1  # Peso mínimo
        analyzer.use_public_api = True  # Força uso da API pública
        analyzer.region = 'frankfurt'  # Região específica
        print("Configurações ajustadas para API pública")
        
        return True
    except Exception as e:
        print(f"Erro na configuração inicial: {e}")
        return False

def verificar_configuracoes():
    try:
        if not setup_inicial():
            return False
        print("\nTestando conexão com API...")
        test_data = analyzer.get_klines('BTCUSDT', '4h')
        if test_data is not None:
            print("Conexão com API OK")
        return True
    except Exception as e:
        print(f"Erro na verificação: {e}")
        return False

def iniciar_monitoramento():
    if verificar_configuracoes():
        monitor_thread = threading.Thread(target=background_monitor, daemon=True)
        monitor_thread.start()
        print("Thread de monitoramento iniciada")
        return True
    return False

# Inicia o monitoramento
iniciar_monitoramento()

# Configura aplicação para o gunicorn
app.config.update({
    'PORT': 10000,
    'host': '0.0.0.0',
    'workers': 1,
    'timeout': 120
})

# Função para criar a aplicação
def create_app():
    return app

# Expõe a aplicação para o gunicorn
application = create_app()