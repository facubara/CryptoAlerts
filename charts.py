# import pandas as pd
# from lightweight_charts import Chart

# if __name__ == '__main__':
#     chart = Chart(title="GIGAUSDC", inner_height= 0.8, inner_width=1)
#     chart.precision(5)
#     df = pd.read_csv('giga_30m_historic.csv')
#     df.rename(columns={'timestamp': 'time'}, inplace=True)
#     df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
#     chart.watermark(text="GIGAUSDC")
#     df2 = pd.read_csv('giga_30m_rsi.csv')
#     df2.rename(columns={'timestamp': 'time'}, inplace=True)
#     print(df2)
#     chart2 = chart.create_subchart(width=1, height=0.2, sync = True)
#     line = chart2.create_line()
#     chart.set(df)
#     line.set(df2)
#     print(line)
#     print(chart2.lines())
#     chart.show(block=True)

import pandas as pd
from lightweight_charts import Chart

def createHorizontalLine(chart, value):
    linehor = chart.create_line(style='dashed')
    horPD = pd.read_csv('giga_30m_rsi.csv')
    horPD.rename(columns={'timestamp': 'time'}, inplace=True)
    horPD.rename(columns={'rsi':'value'}, inplace=True)
    horPD['time'] = pd.to_datetime(df2['time'], unit='s', utc=True)
    horPD['value'] = value
    linehor.set(horPD[['time', 'value']])

if __name__ == '__main__':
    # Create the main chart
    chart = Chart(title="GIGAUSDC", inner_height=0.6, inner_width=1)
    chart.precision(5)

    # Load and prepare the main chart data
    df = pd.read_csv('giga_30m_historic.csv')
    df.rename(columns={'timestamp': 'time'}, inplace=True)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    chart.watermark(text="GIGAUSDC")

    # Load and prepare the RSI data
    df2 = pd.read_csv('giga_30m_rsi.csv')
    df2.rename(columns={'timestamp': 'time'}, inplace=True)
    df2.rename(columns={'rsi':'value'}, inplace=True)
    df2['time'] = pd.to_datetime(df2['time'], unit='s', utc=True)

    # Create a subchart for the RSI
    chart2 = chart.create_subchart(width=1, height=0.4, sync=True)
    chart2.watermark(text="RSI")
    # Create a line for the RSI
    line = chart2.create_line()
    createHorizontalLine(chart2,30)
    createHorizontalLine(chart2,70)

    # Set the data for the main chart and RSI line
    chart.set(df)
    line.set(df2[['time', 'value']])  # Ensure only time and rsi columns are used
    chart2.fit()
    # print(df2)
    # Show the chart
    chart.show(block=True)