from flask import Flask
from pybit.unified_trading import HTTP
import time
import pandas as pd
import threading

app = Flask(__name__)

# === Configuração da API da Bybit ===
API_KEY = "9aiZYfgVZoXUmqLPbW"
API_SECRET = "FJSuBkrW8u23dswPPuik79BSAYtu1qnHXaaI"

session = HTTP(
    testnet=True,
    api_key=API_KEY,
    api_secret=API_SECRET
)

# === Função para buscar velas ===
def get_candles():
    try:
        response = session.get_kline(
            category="linear",
            symbol="BTCUSDT",
            interval="15",
            limit=100
        )
        candles = response['result']['list']
        df = pd.DataFrame(candles, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'  # Corrigido aqui
        ])
        df['close'] = df['close'].astype(float)
        return df
    except Exception as e:
        print(f"Erro ao pegar velas: {e}. Tentando novamente em 10 segundos...")
        time.sleep(10)
        return get_candles()

# === Função principal do robô ===
def executar_robo():
    while True:
        try:
            print("🔄 Verificando sinal...")
            df = get_candles()
            if df is not None:
                ultima = df.iloc[-1]
                print(f"Último fechamento: {ultima['close']}")
                # Aqui entra sua lógica de sinal, compra, venda, etc.
            time.sleep(60)  # Espera 1 minuto antes de verificar novamente
        except Exception as e:
            print(f"[ERRO] {e}")
            time.sleep(15)

# === Rota para manter o Render.com ativo ===
@app.route('/')
def home():
    return 'Robô rodando com sucesso!'

# === Início do robô e do servidor Flask ===
if __name__ == '__main__':
    threading.Thread(target=executar_robo).start()
    app.run(host='0.0.0.0', port=3000)
