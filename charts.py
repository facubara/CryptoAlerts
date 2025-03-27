import pandas as pd
from lightweight_charts import Chart

if __name__ == '__main__':
    chart = Chart(title="GIGAUSDC",scale_candles_only=True)
    chart.precision(5)
    df = pd.read_csv('giga_30m_historic.csv')
    df.rename(columns={'timestamp': 'time'}, inplace=True)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    print(df)
    chart.watermark(text="GIGAUSDC")
    chart.set(df)
    chart.fit()
    chart.show(block=True)