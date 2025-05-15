import os
import logging
import pandas as pd
import pandas_ta as ta

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def is_consolidating(df, percentage=1.5, periods=10):
    recent_candlesticks = df[-periods:]
    
    max_close = recent_candlesticks['Close'].max()
    min_close = recent_candlesticks['Close'].min()

    threshold = 1 - (percentage / 100)
    return min_close > (max_close * threshold)

def is_breaking_out(df, percentage=1.5, consolidation_periods=10, breakout_periods=3, breakout_threshold=2.0):
    if is_consolidating(df[:-breakout_periods], percentage=percentage, periods=consolidation_periods):
        recent_closes = df[-consolidation_periods-breakout_periods:-breakout_periods]
        recent_max = recent_closes['Close'].max()
        
        breakout_closes = df[-breakout_periods:]['Close']
        return any(breakout_closes > recent_max * (1 + breakout_threshold / 100))

    return False

def additional_filters(df):
    # Uptrend filter
    sma50 = df['Close'].rolling(window=50).mean().iloc[-1]
    sma200 = df['Close'].rolling(window=200).mean().iloc[-1]
    price = df['Close'].iloc[-1]
    
    # Check if price is above both SMAs and 50 SMA is above 200 SMA
    uptrend = price > sma50 > sma200
    
    # Volatility filter
    atr = ta.atr(df['High'], df['Low'], df['Close'], length=14).iloc[-1]
    atr_percentage = (atr / price) * 100
    low_volatility = atr_percentage < 3  # Adjust this threshold as needed
    
    return uptrend and low_volatility

def classify_state(df, consolidation_percentage=1.5, breakout_percentage=1.5, 
                   consolidation_periods=10, breakout_periods=3, 
                   breakout_threshold=2.0, volume_factor=1.8):
    
    state = "Neither"
    
    if is_breaking_out(df, percentage=breakout_percentage, 
                       consolidation_periods=consolidation_periods, 
                       breakout_periods=breakout_periods, 
                       breakout_threshold=breakout_threshold): #and additional_filters(df):
        state = "Breaking Out"
        
        # Check for volume confirmation
        recent_volume = df[-breakout_periods:]['Volume'].mean()
        previous_volume = df[-consolidation_periods-breakout_periods:-breakout_periods]['Volume'].mean()
        
        if recent_volume > previous_volume * volume_factor:
            state += " with Volume Confirmation"
    
    elif is_consolidating(df, percentage=consolidation_percentage, periods=consolidation_periods):
        state = "Consolidating"
    
    return state

def analyze_stocks(directory, **kwargs):
    neither_count = 0
    for filename in os.listdir(directory):
        if filename.endswith('.csv'):
            file_path = os.path.join(directory, filename)
            df = pd.read_csv(file_path)
            state = classify_state(df, **kwargs)
            if state != "Neither":
                logging.info(f"{filename}: {state}")
                if state.startswith("Breaking Out"):
                    logging.info(f"  Last close: {df['Close'].iloc[-1]:.2f}")
                    logging.info(f"  Consolidation high: {df['High'].iloc[-kwargs['consolidation_periods']:-kwargs['breakout_periods']].max():.2f}")
                    logging.info(f"  Volume increase: {(df['Volume'].iloc[-kwargs['breakout_periods']:].mean() / df['Volume'].iloc[-kwargs['consolidation_periods']:-kwargs['breakout_periods']].mean() - 1) * 100:.2f}%")
                    logging.info(f"  50 SMA: {df['Close'].rolling(window=50).mean().iloc[-1]:.2f}")
                    logging.info(f"  200 SMA: {df['Close'].rolling(window=200).mean().iloc[-1]:.2f}")
                    atr = ta.atr(df['High'], df['Low'], df['Close'], length=14).iloc[-1]
                    atr_percentage = (atr / df['Close'].iloc[-1]) * 100
                    logging.info(f"  ATR %: {atr_percentage:.2f}%")
            else:
                neither_count += 1
    
    logging.info(f"Number of stocks classified as Neither: {neither_count}")

# Parameters for tweaking
params = {
    'consolidation_percentage': 1.5,
    'breakout_percentage': 1.2,
    'consolidation_periods': 10,
    'breakout_periods': 3,
    'breakout_threshold': 1.1,
    'volume_factor': 1.1
}

# Run the analysis
analyze_stocks('/home/empadgett/myproject/stock_analyzer/sp500pricedata', **params)


