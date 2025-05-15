import yfinance as yf
import pandas as pd
import numpy as np
import mplfinance as mpf
from datetime import datetime, timedelta

ticker="spy"

def detect_gaps(ticker, min_gap_size=0.05):
    try:
        # Fetch data for the last 3 months
        data = yf.download(ticker, period='3mo', interval='1d')
        
        if data.empty or len(data) <= 1:
            print(f"Insufficient data fetched for ticker {ticker}. Please check the ticker symbol or try a different time period.")
            return
        
        data.sort_index(inplace=True)
        data['Low'] = data['Low']
        data['PrevHigh'] = data['High'].shift(1)
        data['High'] = data['High']
        data['PrevLow'] = data['Low'].shift(1)
        
        data['BullishGap'] = (data['Low'] > data['PrevHigh']) & ((data['Low'] - data['PrevHigh']) / data['PrevHigh'] >= min_gap_size)
        data['BearishGap'] = (data['High'] < data['PrevLow']) & ((data['PrevLow'] - data['High']) / data['PrevLow'] >= min_gap_size)

        # Check for gaps in the past 5 days
        five_days_ago = datetime.now().date() - timedelta(days=5)
        last_5_days = data[data.index.date >= five_days_ago]
        gaps_in_last_5_days = last_5_days[last_5_days['BullishGap'] | last_5_days['BearishGap']]
        
        if not gaps_in_last_5_days.empty:
            print(f"Gap(s) occurred in the past 5 days for {ticker}.")


        # Create the plot
        mc = mpf.make_marketcolors(up='g', down='r', inherit=True)
        s  = mpf.make_mpf_style(marketcolors=mc)
        
        additional_plots = [
            mpf.make_addplot((data['BullishGap'] * data['Low']).replace(0, np.nan), scatter=True, markersize=200, marker='^', color='g'),
            mpf.make_addplot((data['BearishGap'] * data['High']).replace(0, np.nan), scatter=True, markersize=200, marker='v', color='r')
        ]
        
        mpf.plot(data, type='candle', style=s, addplot=additional_plots, 
                 title=f'\n{ticker} Price (Gaps ≥ {min_gap_size:.1%} Highlighted)',
                 volume=True, figsize=(12, 8))
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

# Call the function
detect_gaps(ticker, min_gap_size=0.001)  # Set minimum gap size to 0.1%
