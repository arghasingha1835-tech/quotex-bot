import time
import requests
import yfinance as yf
import pandas as pd

# === তোমার টেলিগ্রাম বটের টোকেন ও আইডি এখানে বসাও ===
TELEGRAM_BOT_TOKEN = "8838937230:AAEaskdqCliZylj3WQwDGzy0DsO6sKXxlZg"
TELEGRAM_CHAT_ID = "8724760636"

# যেসব কারেন্সি পেয়ার স্ক্যান করবে
PAIRS = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "EURJPY=X"]

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Error sending message: {e}")

def check_strategy(ticker):
    # ১৫ মিনিটের লাইভ মার্কেট ডেটা
    df = yf.download(ticker, period="3d", interval="15m", progress=False)
    if len(df) < 50:
        return

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # ২০০ EMA ট্রেন্ড ফিল্টার
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()

    # ক্যান্ডেল রেঞ্জ ও উইক ক্যালকুলেশন
    candle_range = df['High'] - df['Low']
    upper_wick = df['High'] - df[['Open', 'Close']].max(axis=1)
    lower_wick = df[['Open', 'Close']].min(axis=1) - df['Low']

    # বিগত ৫ ক্যান্ডেলের সুইং হাই এবং লো
    df['Swing_High'] = df['High'].shift(1).rolling(5).max()
    df['Swing_Low'] = df['Low'].shift(1).rolling(5).min()

    # সদ্য ক্লোজ হওয়া ক্যান্ডেল
    last_candle = df.iloc[-2]
    c_range = candle_range.iloc[-2]

    if c_range == 0:
        return

    # রিভার্সাল ফিল্টার (উইক মিনিমাম ৫৫% + লিকুইডিটি সুইপ)
    bearish_sweep = (last_candle['High'] > last_candle['Swing_High']) and (last_candle['Close'] < last_candle['Swing_High'])
    valid_upper_wick = (upper_wick.iloc[-2] / c_range) >= 0.55
    put_signal = bearish_sweep and valid_upper_wick and (last_candle['Close'] < last_candle['EMA200'])

    bullish_sweep = (last_candle['Low'] < last_candle['Swing_Low']) and (last_candle['Close'] > last_candle['Swing_Low'])
    valid_lower_wick = (lower_wick.iloc[-2] / c_range) >= 0.55
    call_signal = bullish_sweep and valid_lower_wick and (last_candle['Close'] > last_candle['EMA200'])

    pair_name = ticker.replace("=X", "")

    if call_signal:
        msg = f"🚀 *QUOTEX 15M CALL SIGNAL*\n\nPair: *{pair_name}*\nDirection: *CALL (UP)* ⬆️\nExpiry: *15 Minutes*\n\nক্যান্ডেল ওপেনিংয়ে ট্রেড নাও!"
        print(f"Signal found: CALL on {pair_name}")
        send_telegram_alert(msg)

    elif put_signal:
        msg = f"🔻 *QUOTEX 15M PUT SIGNAL*\n\nPair: *{pair_name}*\nDirection: *PUT (DOWN)* ⬇️\nExpiry: *15 Minutes*\n\nক্যান্ডেল ওপেনিংয়ে ট্রেড নাও!"
        print(f"Signal found: PUT on {pair_name}")
        send_telegram_alert(msg)

def run_scanner():
    print("Bot is running... Scanning 15m candles.")
    send_telegram_alert("🤖 *Quotex 15M Scanner Activated!* সিগন্যাল পেলে সাথে সাথে মেসেজ যাবে।")
    
    while True:
        for pair in PAIRS:
            try:
                check_strategy(pair)
            except Exception as e:
                print(f"Error checking {pair}: {e}")
        
        # প্রতি ১৫ মিনিট (৯০০ সেকেন্ড) পর পর স্বয়ংক্রিয়ভাবে স্ক্যান হবে
        time.sleep(900)

if __name__ == "__main__":
    run_scanner()
  
