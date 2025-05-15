import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import os

def calculate_atr(df, period=20):
    """
    Calculate the Average True Range (ATR) for the given DataFrame.
    
    Parameters:
    df (DataFrame): DataFrame containing 'High', 'Low', 'Close' columns.
    period (int): The number of periods to calculate the ATR.
    
    Returns:
    Series: ATR values.
    """
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift(1)).abs()
    low_close = (df['Low'] - df['Close'].shift(1)).abs()
    
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()
    
    return atr

def detect_order_blocks(df):
    """
    Detects order blocks based on ATR and specified candle patterns.
    
    Parameters:
    df (DataFrame): DataFrame containing 'Open', 'High', 'Low', 'Close' columns.
    
    Returns:
    DataFrame: DataFrame with detected order blocks.
    """
    order_blocks = []
    
    # Calculate ATR
    df['ATR'] = calculate_atr(df, period=20)
    
    start_index = max(len(df) - 11, 0) # contrain to past 7 days
    for i in range(start_index, len(df) - 4):
        # Check for the first red candle
        if df['Close'].iloc[i] < df['Open'].iloc[i]:
            # Check for the second red candle
            if (df['Close'].iloc[i + 1] < df['Open'].iloc[i + 1] and 
                df['Close'].iloc[i + 1] < df['Close'].iloc[i]):
                # Check for the third red candle
                if (df['Close'].iloc[i + 2] < df['Open'].iloc[i + 2] and 
                    df['Close'].iloc[i + 2] < df['Close'].iloc[i + 1]):
                    # Check for the fourth green candle
                    if (df['Close'].iloc[i + 3] > df['Open'].iloc[i + 3] and 
                        (df['High'].iloc[i + 3] - df['Low'].iloc[i + 3]) <= df['ATR'].iloc[i + 3] and 
                        df['Open'].iloc[i + 3] > df['Close'].iloc[i]):  # Open > previous red candle close
                        
                        # Check for the fifth green candle
                        if (df['Close'].iloc[i + 4] > df['Open'].iloc[i + 4] and 
                            df['Open'].iloc[i + 4] > df['High'].iloc[i + 2] and 
                            (df['Close'].iloc[i + 4] - df['Open'].iloc[i + 4]) > df['ATR'].iloc[i + 4]* 1.2):
                            order_block_candle = df.iloc[i + 4]
                            order_blocks.append({
                                'Ticker':filename,
                                'Type': 'Bullish',
                                'Price': order_block_candle['Open'],
                                'Date': df['Date'].iloc[i + 4],  # Use the 'Date' 
                            })

    order_blocks_df = pd.DataFrame(order_blocks)
    
    # Debugging: Print the DataFrame
    #print("Detected Order Blocks:")
    #print(order_blocks_df)
    

    return order_blocks_df

def plot_order_blocks(df, order_blocks):
    """
    Plots the candlestick chart with order blocks highlighted using Plotly.
    
    Parameters:
    df (DataFrame): DataFrame containing 'Open', 'High', 'Low', 'Close' columns.
    order_blocks (DataFrame): DataFrame with detected order blocks.
    """
    fig = go.Figure()

    # Add candlestick
    fig.add_trace(go.Candlestick(
        x=df['Date'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Candlestick'
    ))

    # Add bullish order blocks
    if not order_blocks.empty:
        fig.add_trace(go.Scatter(
            x=order_blocks['Date'],
            y=order_blocks['Price'],
            mode='markers',
            marker=dict(size=14, color='black', symbol='triangle-up'),
            name='Bullish Order Blocks'
        
        ))
        print (order_blocks,filename)
        
    # Update layout
    fig.update_layout(
        title='Order Block Detection',
        xaxis_title='Date',
        yaxis_title='Price',
        xaxis_rangeslider_visible=False,
        template='plotly_white'
    )

    fig.show()

    # Directory containing the CSV files
directory = 'sp500pricedata'

# List to hold DataFrames
dataframes = []

# Loop through each file in the directory
for filename in os.listdir(directory):
    if filename.endswith('.csv'):  # Check if the file is a CSV
        file_path = os.path.join(directory, filename)  # Get full file path
        df = pd.read_csv(file_path)  # Read the CSV file into a DataFrame
        df.reset_index(inplace=True)

        # Run order block detection
        order_blocks = detect_order_blocks(df)
        
        if not order_blocks.empty:
            plot_order_blocks(df, order_blocks)


