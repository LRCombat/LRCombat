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
            'timestamp', 'open', 'high', 'low', 'close', 'volume'
        ])
        df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
        return df
    except Exception as e:
        print(f"Erro ao pegar velas: {e}. Tentando novamente em 10s...")
        time.sleep(10)
        return get_candles()

# === Cálculo dos indicadores ===
def calcular_indicadores(df):
    df['EMA20'] = df['close'].ewm(span=20).mean()
    df['EMA50'] = df['close'].ewm(span=50).mean()
    
    # Cálculo do RSI
    delta = df['close'].diff()
    ganho = delta.where(delta > 0, 0)
    perda = -delta.where(delta < 0, 0)
    media_ganho = ganho.rolling(14).mean()
    media_perda = perda.rolling(14).mean()
    rs = media_ganho / media_perda
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Média móvel de volume
    df['volume_ma'] = df['volume'].rolling(20).mean()
    
    # Cálculo do MACD (Moving Average Convergence Divergence)
    df['EMA12'] = df['close'].ewm(span=12).mean()
    df['EMA26'] = df['close'].ewm(span=26).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['MACD_signal'] = df['MACD'].ewm(span=9).mean()

    # Cálculo do ADX (Average Directional Index)
    df['plus_di'] = 100 * (df['high'].diff().where(df['high'].diff() > df['low'].diff(), 0) / df['close']).rolling(14).mean()
    df['minus_di'] = 100 * (df['low'].diff().where(df['low'].diff() > df['high'].diff(), 0) / df['close']).rolling(14).mean()
    df['ADX'] = 100 * (df['plus_di'] - df['minus_di']).abs() / (df['plus_di'] + df['minus_di'])
    
    return df

# === Lógica do robô ===
def verificar_sinal(df):
    ultima = df.iloc[-1]
    anterior = df.iloc[-2]

    # Condições para Compra
    if (ultima['EMA20'] > ultima['EMA50'] and
        anterior['EMA20'] <= anterior['EMA50'] and
        ultima['RSI'] > 50 and
        ultima['volume'] > ultima['volume_ma'] and
        ultima['MACD'] > ultima['MACD_signal'] and
        ultima['ADX'] > 20):
        return "COMPRA"

    # Condições para Venda
    elif (ultima['EMA20'] < ultima['EMA50'] and
          anterior['EMA20'] >= anterior['EMA50'] and
          ultima['RSI'] < 50 and
          ultima['volume'] > ultima['volume_ma'] and
          ultima['MACD'] < ultima['MACD_signal'] and
          ultima['ADX'] > 20):
        return "VENDA"

    return None

# === Execução principal do robô ===
def executar_robo():
    while True:
        try:
            print("🔄 Verificando sinal...")
            df = get_candles()
            df = calcular_indicadores(df)
            sinal = verificar_sinal(df)
            if sinal:
                print(f"🚀 SINAL DETECTADO: {sinal}")
                # Aqui você pode integrar ordens reais ou simulações
            else:
                print("❌ Nenhum sinal agora.")
            time.sleep(60)  # Espera 1 minuto
        except Exception as e:
            print(f"[ERRO] {e}")
            time.sleep(15)

# === Rota para manter ativo no Render ===
@app.route('/')
def home():
    return 'GoldenTrendBot PRO rodando!'

# === Início do robô + servidor Flask ===
if __name__ == '__main__':
    threading.Thread(target=executar_robo).start()
    app.run(host='0.0.0.0', port=3000)
