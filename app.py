from dash import Dash, html, dcc, dash_table
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from technical_analysis import TechnicalAnalysis
from database import SignalDatabase
from datetime import datetime
import threading
import time
from notifications import TelegramNotifier
from price_monitor import PriceMonitor

# Inicialização
db = SignalDatabase()
app = Dash(__name__)
analyzer = TechnicalAnalysis()
price_monitor = PriceMonitor()

# Configuração do Telegram
telegram_token = "7690455274:AAHB64l8csWoE5UpV1Pnn9c8chJzd5sZTXQ"
chat_id = "1249100206"
notifier = TelegramNotifier(telegram_token, chat_id)

def get_expected_variation(symbol):
    try:
        df = analyzer.get_klines(symbol.replace('.P', ''), '1d', limit=30)
        if df is not None and len(df) > 0:
            high = df['high'].max()  # Maior preço em 30 dias
            low = df['low'].min()    # Menor preço em 30 dias
            variation = ((high - low) / low) * 100
            return min(variation, 50)  # Limita a 50% de variação máxima
    except:
        pass
    return 10  # Retorna 10% como valor padrão se houver erro

# Layout do aplicativo
app.layout = html.Div(style={
    'backgroundColor': '#0a1929',
    'minHeight': '100vh',
    'margin': 0,
    'padding': 0,
    'fontFamily': 'Arial'
}, children=[
    # Header com imagem de fundo
    html.Div(style={
        'backgroundImage': 'url("/assets/header_bg.jpg")',
        'backgroundSize': 'cover',
        'backgroundPosition': 'center',
        'height': '200px',
        'position': 'relative',
        'marginBottom': '20px'
    }, children=[
        # Overlay escuro
        html.Div(style={
            'backgroundColor': 'rgba(0,0,0,0.5)',
            'position': 'absolute',
            'top': 0,
            'left': 0,
            'right': 0,
            'bottom': 0,
            'display': 'flex',
            'flexDirection': 'column',
            'justifyContent': 'center',
            'alignItems': 'center'
        }, children=[
            html.H1("KcryptoN", style={
                'color': '#00ffff',
                'fontSize': '48px',
                'textShadow': '0 0 10px rgba(0,255,255,0.5)',
                'marginBottom': '10px'
            }),
            html.H2("Disciplina e Persistência Levam ao Sucesso Financeiro", style={
                'color': '#ffffff',
                'fontSize': '18px',
                'fontWeight': 'normal',
                'textShadow': '0 0 5px rgba(255,255,255,0.5)'
            })
        ])
    ]),

    # Painel de Estatísticas
    html.Div(style={
        'display': 'flex',
        'gap': '20px',
        'padding': '20px',
        'maxWidth': '1400px',
        'margin': '0 auto',
    }, children=[
        html.Div(style={
            'flex': '1',
            'backgroundColor': '#0f2744',
            'borderRadius': '15px',
            'padding': '20px',
        }, children=[
            html.H3("Estatísticas Gerais", style={
                'color': '#ffffff',
                'fontSize': '18px',
                'marginBottom': '15px'
            }),
            html.Div(id='stats-container', style={
                'display': 'grid',
                'gridTemplateColumns': 'repeat(3, 1fr)',
                'gap': '15px'
            })
        ])
    ]),

    # Conteúdo Principal
    html.Div(style={
        'display': 'flex',
        'padding': '20px',
        'maxWidth': '1400px',
        'margin': '0 auto',
        'gap': '20px',
        'maxHeight': 'calc(100vh - 400px)',  # Ajuste para altura máxima
        'overflowY': 'auto'  # Adiciona barra de rolagem vertical
    }, children=[
        # Coluna Esquerda - Sinais Ativos
        html.Div(style={
            'flex': '1',
            'backgroundColor': '#0f2744',
            'borderRadius': '15px',
            'padding': '20px',
        }, children=[
            html.Div([
                "Última atualização: ",
                html.Span(id='last-update', style={'color': '#ffffff'})
            ], style={
                'color': '#8b9cc4',
                'textAlign': 'center',
                'marginBottom': '20px',
                'fontSize': '14px'
            }),
            html.Div([
                "Sinais Ativos ",
                html.Span(id='signal-count')
            ], style={
                'color': '#ffffff',
                'fontSize': '20px',
                'marginBottom': '15px',
                'borderBottom': '2px solid #1a3958',
                'paddingBottom': '5px'
            }),
            html.Div(
                id='signals-container',
                style={
                    'maxHeight': '70vh',
                    'overflowY': 'auto',
                    'scrollbarWidth': 'thin',
                    'scrollbarColor': '#1a3958 #0f2744'
                }
            )
        ]),
        
        # Coluna Direita - Histórico
        html.Div(style={
            'flex': '1',
            'backgroundColor': '#0f2744',
            'borderRadius': '15px',
            'padding': '20px',
        }, children=[
            html.H2("Histórico de Sinais", style={
                'color': '#ffffff',
                'fontSize': '20px',
                'marginBottom': '20px',
                'borderBottom': '2px solid #1a3958',
                'paddingBottom': '5px'
            }),
            html.Div(
                id='historical-container',
                style={
                    'maxHeight': '80vh',
                    'overflowY': 'auto',
                    'scrollbarWidth': 'thin',
                    'scrollbarColor': '#1a3958 #0f2744'
                }
            )
        ])
    ]),

    # Projeção de Resultados
    html.Div(style={
        'padding': '20px',
        'maxWidth': '1400px',
        'margin': '0 auto',
    }, children=[
        html.Div(style={
            'backgroundColor': '#0f2744',
            'borderRadius': '15px',
            'padding': '20px',
            'maxHeight': '400px',  # Altura máxima para a tabela
            'overflowY': 'auto'  # Adiciona barra de rolagem vertical
        }, children=[
            html.H2("Projeção de Resultados", style={
                'color': '#ffffff',
                'fontSize': '20px',
                'marginBottom': '20px',
                'borderBottom': '2px solid #1a3958',
                'paddingBottom': '5px'
            }),
            html.Div(id='results-projection-container', style={
                'overflowX': 'auto'  # Adiciona barra de rolagem horizontal se necessário
            })
        ])
    ]),
    dcc.Interval(id='interval-component', interval=1000)
])

@app.callback(
    [Output('signals-container', 'children'),
     Output('signal-count', 'children'),
     Output('historical-container', 'children'),
     Output('last-update', 'children')],
    Input('interval-component', 'n_intervals')
)
def update_signals(_):
    try:
        current_time = datetime.now().strftime('%H:%M:%S')
        active_signals = db.get_recent_signals(hours=24)
        print(f"Sinais ativos encontrados: {len(active_signals)}")  # Debug
        print(f"Sinais: {active_signals}")  # Debug
        
        historical_signals = db.get_historical_signals()
        
        signals = []
        for signal in active_signals:
            is_long = signal['type'] == 'LONG'
            emoji = "🟢" if is_long else "🔴"
            direction = "para cima" if is_long else "para baixo"
            
            card = html.Div([
                html.Div([
                    html.Span(f"{emoji} Ativo: {signal['symbol'].replace('.P', '')}", style={
                        'color': '#ffffff',
                        'fontSize': '18px',
                        'fontWeight': 'bold',
                        'display': 'block',
                        'marginBottom': '5px'
                    }),
                    html.Span(f"⏱ Candle: {datetime.strptime(signal['timestamp'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')}", style={
                        'color': '#8b9cc4',
                        'display': 'block',
                        'marginBottom': '5px'
                    }),
                    html.Span(f"🤖 KryptonBot confirmado {direction}", style={
                        'color': '#ffffff'
                    })
                ])
            ], style={
                'backgroundColor': '#1a3958',
                'padding': '15px',
                'borderRadius': '10px',
                'marginBottom': '10px'
            })
            
            signals.append(card)
        
        count = len(signals)
        
        historical_table = dash_table.DataTable(
            data=[{
                'Par': s['symbol'].replace('.P', ''),
                'Tipo': s['type'],
                'Preço': f"{s['price']:.8f}",
                'Data': datetime.strptime(s['timestamp'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m %H:%M'),
                'Dia': s['days_active']
            } for s in historical_signals],
            columns=[
                {'name': 'Par', 'id': 'Par'},
                {'name': 'Tipo', 'id': 'Tipo'},
                {'name': 'Preço', 'id': 'Preço'},
                {'name': 'Data', 'id': 'Data'},
                {'name': 'Dia', 'id': 'Dia'}
            ],
            style_header={
                'backgroundColor': '#1a3958',
                'color': '#ffffff',
                'fontWeight': 'bold',
                'textAlign': 'center'
            },
            style_cell={
                'backgroundColor': '#0f2744',
                'color': '#ffffff',
                'textAlign': 'center',
                'padding': '10px',
                'fontSize': '14px'
            }
        )
        
        return signals, f"({count})", historical_table, current_time
    except Exception as e:
        print(f"Erro ao atualizar interface: {e}")
        return [], "(0)", [], datetime.now().strftime('%H:%M:%S')

@app.callback(
    Output('results-projection-container', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_results_projection(_):
    try:
        active_signals = db.get_recent_signals(hours=24)
        data = []
        
        for s in active_signals:
            variation = get_expected_variation(s['symbol'])
            leverage_result = variation * 50
            profit = 1000 * (leverage_result / 100)
            
            if s['type'] == 'SHORT':
                variation = -variation
                leverage_result = -leverage_result
                profit = -profit
            
            data.append({
                'Par': s['symbol'].replace('.P', ''),
                'Tipo': s['type'],
                'Entrada': f"${s['price']:.4f}",
                'Saída Proj.': f"${s['price'] * (1 + variation/100):.4f}",
                'Variação': f"{variation:+.2f}%",
                'Alavancagem 50x': f"{leverage_result:+.2f}%",
                'Investimento Base $1000': f"${profit:.2f}"
            })
        
        return dash_table.DataTable(
            data=data,
            columns=[
                {'name': 'Par', 'id': 'Par'},
                {'name': 'Tipo', 'id': 'Tipo'},
                {'name': 'Preço Entrada', 'id': 'Entrada'},
                {'name': 'Preço Saída (Proj.)', 'id': 'Saída Proj.'},
                {'name': 'Variação', 'id': 'Variação'},
                {'name': 'Alavancagem 50x', 'id': 'Alavancagem 50x'},
                {'name': 'Investimento Base $1000', 'id': 'Investimento Base $1000'}
            ],
            style_header={
                'backgroundColor': '#1a3958',
                'color': '#ffffff',
                'fontWeight': 'bold',
                'textAlign': 'center'
            },
            style_cell={
                'backgroundColor': '#0f2744',
                'color': '#ffffff',
                'textAlign': 'center',
                'padding': '10px',
                'fontSize': '14px',
                'minWidth': '100px'  # Largura mínima para as células
            }
        )
    except Exception as e:
        print(f"Erro ao atualizar projeção: {e}")
        return []
def background_monitor():
    while True:
        try:
            print("\n=== Nova rodada de monitoramento ===")
            current_time = datetime.now().strftime('%H:%M:%S')
            print(f"Hora: {current_time}")
            
            print("\nVerificando pares:")
            total_pares = len(analyzer.futures_pairs)
            
            for idx, symbol in enumerate(analyzer.futures_pairs, 1):
                print(f"\rAnalisando: {symbol} [{idx}/{total_pares}]", end="", flush=True)
                
                for tf in analyzer.timeframes:
                    try:
                        df = analyzer.get_klines(symbol.replace('.P', ''), tf)
                        if df is not None and len(df) >= 20:
                            df = analyzer.calculate_supertrend(df)
                            signal = analyzer.check_signal(df)
                            
                            if signal and signal in ['LONG', 'SHORT']:  # Verifica se o sinal é válido
                                signal_data = {
                                    'symbol': symbol,
                                    'type': signal,
                                    'price': float(df['close'].iloc[-1]),
                                    'timeframe': tf,
                                    'timestamp': datetime.now()
                                }
                                
                                try:
                                    notifier.send_signal(signal_data)
                                    print("\nSinal enviado para Telegram com sucesso!")
                                except Exception as e:
                                    print(f"\nErro ao enviar para Telegram: {e}")
                                
                                try:
                                    db.add_signal(signal_data)
                                    print("Sinal salvo no banco de dados!")
                                except Exception as e:
                                    print(f"\nErro ao salvar no banco: {e}")
                                
                                print(f"\n🔔 SINAL ENCONTRADO!")
                                print(f"   Par: {symbol}")
                                print(f"   Tipo: {signal}")
                                print(f"   TF: {tf}")
                                print(f"   Preço: {df['close'].iloc[-1]:.8f}")
                                print("-" * 50)
                    except Exception as e:
                        print(f"\nErro ao analisar {symbol} em {tf}: {str(e)}")
                        continue
            
            print("\n\nVerificação completa. Aguardando próximo ciclo...")
            time.sleep(300)
            
        except Exception as e:
            print(f"\nErro no monitoramento: {e}")
            time.sleep(60)

def start_monitoring():
    print("\nIniciando sistema de monitoramento...")
    monitor_thread = threading.Thread(target=background_monitor, daemon=True)
    monitor_thread.start()
    print("Monitoramento iniciado com sucesso!")

if __name__ == '__main__':
    print("\n=== Iniciando KryptoN Trading Bot ===")
    start_monitoring()
    app.run_server(debug=False)