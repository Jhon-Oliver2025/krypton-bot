from app import app, start_monitoring

# Inicia o monitoramento
monitor = start_monitoring()

# Expõe o servidor para o gunicorn
server = app.server