import ccxt
import pandas as pd
import math
import requests
from datetime import datetime, timedelta, timezone
import time

# Configuration
BOT_TOKEN = '7514996270:AAEhxqAeMePmunqCyHDPN_di5TGpnl1LzoA'
CHAT_ID = 431930778
NUMBER_OF_CANDLES = 350
TIMEFRAME = '30m'
CSV_FILE = 'giga_30m_historic.csv'
BEGINNING_TIMESTAMP = 1733936400  # Example beginning timestamp

def send_telegram_message(token, chat_id, message):
    """Send a message to a Telegram chat."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': message}
    response = requests.post(url, data=payload)
    return response.json()

def get_unix_timestamp(dt):
    """Convert a datetime object to a Unix timestamp."""
    return int(dt.timestamp())

def calculate_timestamps(start_timestamp, number_of_candles):
    """Calculate end timestamps for the API request."""
    end_time = start_timestamp + number_of_candles * 30 * 60
    return end_time
    # return get_unix_timestamp(end_time)

def fetch_candles(start, end, timeframe):
    """Fetch candle data from the API and convert it to a DataFrame."""
    url = f"https://api.coinbase.com/api/v3/brokerage/market/products/GIGA-USD/candles?granularity=THIRTY_MINUTE&start={start}&end={end}"
    try:
        print(url)
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        candles = data.get('candles', [])
        print(candles)
        df = pd.DataFrame(candles).iloc[::-1]
        print(df)
        df.rename(columns={'start': 'timestamp'}, inplace=True)
        # df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].apply(pd.to_numeric)
        return df
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return pd.DataFrame()

def calculate_rsi(data, period=14):
    """Calculate the RSI for the given data."""
    delta = data['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(com=period-1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period-1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def wait_until_next_half_hour():
    """Wait until the next :00 or :30 mark."""
    now = datetime.now(timezone.utc)
    next_run = now.replace(minute=30, second=0, microsecond=0) if now.minute < 30 else (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    wait_time = (next_run - now).total_seconds()
    print(f"Waiting for {wait_time} seconds until the next :00 or :30 mark.")
    time.sleep(wait_time)

def check_rsi():
    """Check the RSI and send alerts if necessary."""
    wait_until_next_half_hour()
    send_telegram_message(BOT_TOKEN, CHAT_ID, f"Start new run timeframe: {TIMEFRAME}")
    while True:
        try:
            start, end = calculate_timestamps(NUMBER_OF_CANDLES)
            df = fetch_candles(start, end, 'THIRTY_MINUTE')
            if df.empty:
                print("No data fetched.")
                continue
            df['rsi'] = calculate_rsi(df)
            latest_rsi = df['rsi'].iloc[-1]
            telegram_timestamp = (datetime.now(timezone.utc) - timedelta(minutes=30)).replace(second=0, microsecond=0)
            send_telegram_message(BOT_TOKEN, CHAT_ID, f"{telegram_timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')} Latest RSI: {latest_rsi}")
            if latest_rsi < 30:
                print("RSI is oversold!")
            elif latest_rsi > 70:
                print("RSI is overbought!")
        except Exception as e:
            print(f"An error occurred: {e}")
        wait_until_next_half_hour()

def update_historic(csv_file, number_of_candles, timeframe_minutes, beginning_timestamp):
    """Update the CSV file with the latest candlestick data."""
    try:
        existing_data = pd.read_csv(csv_file, parse_dates=['timestamp'], date_format=pd.Timestamp)
        latest_timestamp = existing_data['timestamp'].max() if not existing_data.empty else datetime.fromtimestamp(beginning_timestamp, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        next_run = now.replace(minute=30, second=0, microsecond=0) if now.minute < 30 else (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        print(f"int next_run: {int(next_run.timestamp())}")
        print(f"int latesttimestamp: {latest_timestamp}")
        while (int(latest_timestamp) + 30*60 < get_unix_timestamp(next_run)):
            print(f"latest_timestamp: {datetime.fromtimestamp(int(latest_timestamp), tz=timezone.utc)}")
            start = int(latest_timestamp) + 30*60
            end = calculate_timestamps(start, number_of_candles)
            print(f"start: {datetime.fromtimestamp(start, tz=timezone.utc)}")
            print(f"end: {datetime.fromtimestamp(end, tz=timezone.utc)}")
            new_data = fetch_candles(start, end, f"{timeframe_minutes}_MINUTE")
            print(new_data)
            if new_data.empty:
                break
            new_data.to_csv(csv_file,mode='a', index=False, header=False)
            latest_timestamp = new_data['timestamp'].max()
            print("CSV file updated successfully.")
    except (FileNotFoundError, pd.errors.EmptyDataError):
        print("CSV file not found or empty. Creating a new one from the beginning timestamp.")
        start = beginning_timestamp
        end = calculate_timestamps(start, number_of_candles)
        print(f"start: {start}")
        print(f"end: {end}")
        new_data = fetch_candles(start, end, f"{timeframe_minutes}_MINUTE")
        new_data.to_csv(csv_file, index=False)
        print("New CSV file created.")

if __name__ == "__main__":
    update_historic(CSV_FILE, NUMBER_OF_CANDLES, 30, BEGINNING_TIMESTAMP)
    # check_rsi()