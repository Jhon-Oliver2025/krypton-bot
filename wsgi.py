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

# Expõe a aplicação para o gunicorn
server = app.server
application = server

flask==2.0.1
python-binance==1.0.16
gunicorn==21.2.0# Expõe o servidor para o gunicorn
from app import app

# Expõe o servidor para o gunicorn
server = app.server

if __name__ == "__main__":
    app.run_server(host='0.0.0.0', port=10000)