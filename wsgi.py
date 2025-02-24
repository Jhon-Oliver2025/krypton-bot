from app import app, start_monitoring, background_monitor, analyzer, db
import threading
import time

print("=== Iniciando KryptoN Trading Bot ===")

def iniciar_monitoramento_com_retry():
    while True:
        try:
            print("\nIniciando sistema de monitoramento...")
            print(f"Pares disponíveis: {len(analyzer.futures_pairs)}")
            print(f"Timeframes configurados: {analyzer.timeframes}")
            
            # Verifica conexão com banco de dados
            try:
                db.get_recent_signals(hours=24)
                print("Conexão com banco de dados OK")
            except Exception as e:
                print(f"Erro no banco de dados: {e}")
            
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