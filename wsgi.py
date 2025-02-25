from app import app, start_monitoring, background_monitor, analyzer, db, notifier
import threading
import time

print("=== Iniciando KryptoN Trading Bot ===")

def iniciar_monitoramento_com_retry():
    while True:
        try:
            print("\nIniciando sistema de monitoramento...")
            monitor_thread = threading.Thread(target=background_monitor, daemon=True)
            monitor_thread.start()
            print("Thread de monitoramento iniciada com sucesso")
            break
        except Exception as e:
            print(f"Erro ao iniciar monitoramento: {e}")
            print("Tentando novamente em 10 segundos...")
            time.sleep(10)

# Inicia o monitoramento em uma thread separada
iniciar_monitoramento_com_retry()

# Expõe o servidor para o gunicorn
server = app.server

if __name__ == "__main__":
    app.run_server(debug=False, host='0.0.0.0', port=10000)