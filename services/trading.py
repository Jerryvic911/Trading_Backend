import pandas as pd
import requests
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD
from ta.volatility import BollingerBands

# ----------------------------
# CONFIGURATION
# ----------------------------
API_KEY = "8502b0dc5ade44bca15fbe5c559a8e51"

BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

PAIR = "EUR/USD"
EXPIRY = 1        # Trade duration in minutes
PREP_TIME = 2     # Minutes before entry
COUNTDOWN = 30    # Seconds before entry to send reminder

#bot = Bot(token=BOT_TOKEN)

# ----------------------------
# GET FOREX DATA
# ----------------------------
def get_data():
    url = f"https://api.twelvedata.com/time_series?symbol={PAIR}&interval=1min&outputsize=200&apikey={API_KEY}"
    r = requests.get(url).json()
    
    if "values" not in r:
        print("API Error:", r)
        return None

    df = pd.DataFrame(r["values"])
    df = df.iloc[::-1]  # oldest first

    # Convert numeric columns to float
    df["close"] = df["close"].astype(float)
    df["open"] = df["open"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)

    return df

# ----------------------------
# CANDLESTICK CONFIRMATION
# ----------------------------
def candle_confirmation(df):
    if len(df) < 2:
        return None
    last = df.iloc[-1]
    prev = df.iloc[-2]
    # Bullish engulfing
    if last['close'] > last['open'] and prev['close'] < prev['open'] and last['close'] > prev['open']:
        return "CALL"
    # Bearish engulfing
    if last['close'] < last['open'] and prev['close'] > prev['open'] and last['close'] < prev['open']:
        return "PUT"
    return None

# ----------------------------
# CALCULATE SIGNAL
# ----------------------------
def get_signal(df):
    score = 0
    last = df.iloc[-1]

    # EMA Trend
    ema20 = EMAIndicator(df["close"], window=20).ema_indicator()
    ema50 = EMAIndicator(df["close"], window=50).ema_indicator()
    ema200 = EMAIndicator(df["close"], window=200).ema_indicator()
    last_ema20 = ema20.iloc[-1]
    last_ema50 = ema50.iloc[-1]
    last_ema200 = ema200.iloc[-1]

    if last_ema20 > last_ema50 > last_ema200:
        ema_signal = "CALL"
        score += 2
    elif last_ema20 < last_ema50 < last_ema200:
        ema_signal = "PUT"
        score += 2
    else:
        ema_signal = "WAIT"

    # RSI
    rsi = RSIIndicator(df["close"], window=14).rsi().iloc[-1]
    if rsi < 30:
        rsi_signal = "CALL"
        score += 1
    elif rsi > 70:
        rsi_signal = "PUT"
        score += 1
    else:
        rsi_signal = "WAIT"

    # Bollinger Bands
    bb = BollingerBands(df["close"], window=20, window_dev=2)
    last_bb_low = bb.bollinger_lband().iloc[-1]
    last_bb_high = bb.bollinger_hband().iloc[-1]

    if last["close"] <= last_bb_low:
        bb_signal = "CALL"
        score += 1
    elif last["close"] >= last_bb_high:
        bb_signal = "PUT"
        score += 1
    else:
        bb_signal = "WAIT"

    # MACD
    macd = MACD(df["close"])
    macd_signal = "WAIT"
    if macd.macd_diff().iloc[-1] > 0:
        macd_signal = "CALL"
        score += 1
    elif macd.macd_diff().iloc[-1] < 0:
        macd_signal = "PUT"
        score += 1

    # ADX proxy
    adx = df["close"].diff().abs().rolling(14).mean().iloc[-1]
    if adx > 0.0005:
        score += 1

    # Candlestick confirmation
    candle_signal = candle_confirmation(df)
    if candle_signal is not None:
        score += 1

    # Combine signals (send only if score >= 5)
    if score >= 5:
        if ema_signal == "CALL" or rsi_signal == "CALL" or bb_signal == "CALL" or macd_signal == "CALL" or candle_signal == "CALL":
            return "CALL", score
        elif ema_signal == "PUT" or rsi_signal == "PUT" or bb_signal == "PUT" or macd_signal == "PUT" or candle_signal == "PUT":
            return "PUT", score

    return "WAIT", score

# ----------------------------
# SEND TELEGRAM SIGNAL
# ----------------------------
#
def generate_signal():
    df = get_data()
    
    if df is None:
        return None, None

    signal, score = get_signal(df)
    return signal, score