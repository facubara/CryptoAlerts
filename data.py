import ccxt
import pandas as pd
import math
import requests
from datetime import datetime, timedelta, timezone
import time
from dotenv import load_dotenv
from colorama import Fore, Style, init
import os


# Initialize colorama
init(autoreset=True)

# Configuration
NUMBER_OF_CANDLES = 350
TIMEFRAME = '30m'
CSV_FILE = 'giga_30m_historic.csv'
RSI_CSV_FILE = 'giga_30m_rsi.csv'
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
        df = pd.DataFrame(candles).iloc[::-1]
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
        # print(f"int next_run: {int(next_run.timestamp())}")
        # print(f"int latesttimestamp: {latest_timestamp}")
        while (int(latest_timestamp) + 30*60 < get_unix_timestamp(next_run)):
            # print(f"latest_timestamp: {datetime.fromtimestamp(int(latest_timestamp), tz=timezone.utc)}")
            start = int(latest_timestamp) + 30*60
            end = calculate_timestamps(start, number_of_candles)
            # print(f"start: {datetime.fromtimestamp(start, tz=timezone.utc)}")
            # print(f"end: {datetime.fromtimestamp(end, tz=timezone.utc)}")
            new_data = fetch_candles(start, end, f"{timeframe_minutes}_MINUTE")
            if new_data.empty:
                break
            new_data.to_csv(csv_file,mode='a', index=False, header=False)
            latest_timestamp = new_data['timestamp'].max()
            print("CSV file updated successfully.")
    except (FileNotFoundError, pd.errors.EmptyDataError):
        print("CSV file not found or empty. Creating a new one from the beginning timestamp.")
        start = beginning_timestamp
        end = calculate_timestamps(start, number_of_candles)
        # print(f"start: {start}")
        # print(f"end: {end}")
        new_data = fetch_candles(start, end, f"{timeframe_minutes}_MINUTE")
        new_data.to_csv(csv_file, index=False)
        print("New CSV file created.")

def update_rsi(rsi_csv_file):
    df = pd.read_csv('giga_30m_historic.csv')
    df['rsi'] = calculate_rsi(df)
    df = df[['timestamp', 'rsi']]
    df.to_csv(rsi_csv_file, index=False)
    # existing_data = pd.read_csv(rsi_csv_file, parse_dates=['timestamp'], date_format=pd.Timestamp)
    # latest_timestamp = existing_data['timestamp'].max() if not existing_data.empty else datetime.fromtimestamp(beginning_timestamp, tz=timezone.utc)



def simulate_portfolio(portfolio_size, rsi_level_1, rsi_level_2, transaction_file):
    """Simulate a portfolio and execute trades based on RSI levels."""
    # Initialize portfolio
    cash = portfolio_size
    holdings = 0
    transaction_log = []

    # Load historical data
    df = pd.read_csv(CSV_FILE)
    df['rsi'] = calculate_rsi(df)

    with open(transaction_file, 'w') as file:
        file.write("Timestamp,Action,Amount,Price,Gain/Loss\n")

        for index, row in df.iterrows():
            current_rsi = row['rsi']
            current_price = row['close']
            gain_loss = 0

            # Buy condition
            if current_rsi < rsi_level_1 and cash > 0:
                # Buy as much as possible with available cash
                amount_to_buy = cash / current_price
                holdings += amount_to_buy
                cash = 0
                transaction_log.append((row['timestamp'], 'BUY', amount_to_buy, current_price, gain_loss))
                file.write(f"{row['timestamp']},BUY,{amount_to_buy},{current_price},{gain_loss}\n")
                print(f"{Fore.GREEN}Bought {Fore.CYAN}{amount_to_buy} units {Fore.RESET}at {Fore.MAGENTA}{current_price} {Fore.RESET}on {row['timestamp']}")

            # Sell condition
            elif current_rsi > rsi_level_2 and holdings > 0:
                # Calculate gain/loss
                gain_loss = (current_price - transaction_log[-1][3]) * holdings
                # Sell all holdings
                cash += holdings * current_price
                transaction_log.append((row['timestamp'], 'SELL', holdings, current_price, gain_loss))
                file.write(f"{row['timestamp']},SELL,{holdings},{current_price},{gain_loss}\n")
                gain_loss_color = Fore.GREEN if gain_loss >= 0 else Fore.RED
                print(f"{Fore.RED}Sold {Fore.CYAN}{holdings} units {Fore.RESET}at {Fore.MAGENTA}{current_price} {Fore.RESET}on {row['timestamp']} with gain/loss: {gain_loss_color}{gain_loss}")
                holdings = 0

    # Final portfolio value
    final_value = cash + holdings * df.iloc[-1]['close']
    percentage_change = ((final_value - portfolio_size) / portfolio_size) * 100
    percentage_color = Fore.GREEN if percentage_change >= 0 else Fore.RED
    print(f"Final portfolio value: {Fore.GREEN if final_value >= portfolio_size else Fore.RED}{final_value:.2f}")
    print(f"Percentage change: {percentage_color}{percentage_change:.2f}%")
    return transaction_log, final_value


def test_simulate_portfolio(portfolio_size, rsi_level_1, rsi_level_2, df_rsi, df):
    """Simulate a portfolio and execute trades based on RSI levels."""
    cash = portfolio_size
    holdings = 0

    for index, row in df_rsi.iterrows():
        current_rsi = row['value']
        current_price = df.loc[df['time'] == row['time'], 'close'].values[0]

        # Buy condition
        if current_rsi < rsi_level_1 and cash > 0:
            amount_to_buy = cash / current_price
            holdings += amount_to_buy
            cash = 0

        # Sell condition
        elif current_rsi > rsi_level_2 and holdings > 0:
            cash += holdings * current_price
            holdings = 0

    final_value = cash + holdings * df.iloc[-1]['close']
    percentage_change = ((final_value - portfolio_size) / portfolio_size) * 100
    return percentage_change

def find_best_thresholds(portfolio_size, df_rsi, df, low_range, high_range, output_file):
    """Find the best RSI thresholds for maximizing portfolio gains."""
    best_gain = float('-inf')
    best_low = None
    best_high = None

    with open(output_file, 'w') as file:
        file.write("Low Threshold,High Threshold,Percentage Change\n")

        for low in low_range:
            for high in high_range:
                if low >= high:
                    continue

                percentage_change = test_simulate_portfolio(portfolio_size, low, high, df_rsi, df)
                file.write(f"{low},{high},{percentage_change:.2f}\n")

                if percentage_change > best_gain:
                    best_gain = percentage_change
                    best_low = low
                    best_high = high

    return best_low, best_high, best_gain

if __name__ == "__main__":
    load_dotenv()

    BOT_TOKEN = os.getenv('API_KEY')
    CHAT_ID = os.getenv('CHAT_ID')
    update_historic(CSV_FILE, NUMBER_OF_CANDLES, 30, BEGINNING_TIMESTAMP)
    update_rsi(RSI_CSV_FILE)

     # Simulate portfolio
    # portfolio_size = 1000  # Example portfolio size
    # rsi_level_1 = 30  # RSI level to buy
    # rsi_level_2 = 70  # RSI level to sell
    # transaction_file = 'transaction_log.txt'
    # transaction_log, final_value = simulate_portfolio(portfolio_size, rsi_level_1, rsi_level_2, transaction_file)

    # # Define parameters
    # portfolio_size = 10000  # Example portfolio size
    # low_range = range(10, 50, 1)  # Example range for low thresholds
    # high_range = range(50, 90, 1)  # Example range for high thresholds
    # output_file = 'threshold_results.txt'
    # # Load data
    # df = pd.read_csv('giga_30m_historic.csv')
    # df.rename(columns={'timestamp': 'time'}, inplace=True)
    # df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    # df_rsi = pd.read_csv('giga_30m_rsi.csv')
    # df_rsi.rename(columns={'timestamp': 'time'}, inplace=True)
    # df_rsi.rename(columns={'rsi':'value'}, inplace=True)
    # df_rsi = df_rsi.dropna(subset=['value'])
    # df_rsi['time'] = pd.to_datetime(df_rsi['time'], unit='s', utc=True)
    # # Find the best thresholds

    # best_low, best_high, best_gain = find_best_thresholds(portfolio_size, df_rsi, df, low_range, high_range, output_file)

    # # Print the best result
    # print(f"Best Low Threshold: {best_low}, Best High Threshold: {best_high}, Best Gain: {best_gain:.2f}%")
    # Print transaction log
    # for transaction in transaction_log:
    #     print(transaction)
    # check_rsi()