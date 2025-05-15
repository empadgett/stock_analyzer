import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from finta import TA
import os

def calculate_hma(df):
    n1 = 5  # Shorter moving average period
    n2 = 34  # Longer moving average period
    df['HMA1'] = TA.HMA(df, period=n1)
    df['HMA2'] = TA.HMA(df, period=n2)
    return df

def detect_confirmed_hull_xover(df, n):
    df = calculate_hma(df)
    confirmed_crossovers = []
    
    # Check for crossovers in the last 'n' entries
    recent_hma1 = df['HMA1'].tail(n)
    recent_hma2 = df['HMA2'].tail(n)
    
    for i in range(1, len(recent_hma1)):
        crossover_date = recent_hma1.index[i].date()
        latest_close = df['Close'].iloc[-1]
        
        # Bullish crossover
        if (recent_hma1.iloc[i-1] < recent_hma2.iloc[i-1] and recent_hma1.iloc[i] > recent_hma2.iloc[i]):
            # Check CAHOLD condition
            low_day_index = df['Low'].loc[crossover_date:].idxmin()
            high_of_low_day = df.loc[low_day_index, 'High']
            
            if latest_close > high_of_low_day:
                confirmed_crossovers.append((crossover_date, 'Bullish'))
        
        # Bearish crossover
        elif (recent_hma1.iloc[i-1] > recent_hma2.iloc[i-1] and recent_hma1.iloc[i] < recent_hma2.iloc[i]):
            # Check CBLOHD condition
            high_day_index = df['High'].loc[crossover_date:].idxmax()
            low_of_high_day = df.loc[high_day_index, 'Low']
            
            if latest_close < low_of_high_day:
                confirmed_crossovers.append((crossover_date, 'Bearish'))

    return confirmed_crossovers, df
    
directory = '/home/empadgett/myproject/sp500pricedata'
n = 5

confirmed_stocks = []

for filename in os.listdir(directory):
    if filename.endswith('.csv'):
        file_path = os.path.join(directory, filename)
        df = pd.read_csv(file_path, parse_dates=['Date'], index_col='Date')
        confirmed_crossovers, df = detect_confirmed_hull_xover(df, n)
        
        if confirmed_crossovers:
            stock_name = filename.split('.')[0]
            for date, direction in confirmed_crossovers:
                confirmed_stocks.append((stock_name, date, direction, df))

if confirmed_stocks:
    print("Stocks with confirmed Hull MA crossovers:")
    for stock, date, direction, df in confirmed_stocks:
        print(f"{stock}: Confirmed {direction} on {date}")

else:
    print("No stocks with confirmed Hull MA crossovers found.")




