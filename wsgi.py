from app import app, start_monitoring, background_monitor, analyzer, db
import threading
import time

print("=== Iniciando KryptoN Trading Bot ===")

def verificar_configuracoes():
    try:
        # Verifica configurações do analyzer
        print(f"\nPares disponíveis: {len(analyzer.futures_pairs)}")
        print("Exemplo de pares:", analyzer.futures_pairs[:3])
        print(f"Timeframes configurados: {analyzer.timeframes}")
        
        # Verifica Telegram
        print("\nVerificando configuração do Telegram...")
        if hasattr(notifier, 'telegram_token'):
            print("Token do Telegram configurado")
        
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