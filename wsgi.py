from app import app, start_monitoring, background_monitor, analyzer, db, notifier
import threading
import time

print("=== Iniciando KryptoN Trading Bot ===")

def setup_inicial():
    try:
        print("\nConfigurando sistema...")
        analyzer.futures_pairs = ['BTCUSDT']
        analyzer.period = '1'
        analyzer.retry_delay = 7200
        analyzer.timeout = 5
        analyzer.use_spot = True
        analyzer.api_weight = 1
        analyzer.use_public_api = True
        analyzer.region = 'frankfurt'
        return True
    except Exception as e:
        print(f"Erro na configuração inicial: {e}")
        return False

# Configura e inicia o monitoramento
setup_inicial()

# Configuração do servidor WSGI
application = app.server

if __name__ == "__main__":
    app.run_server(debug=False, host='0.0.0.0', port=10000)