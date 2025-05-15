import yfinance as yf
import pandas as pd
import time

def get_stock_info(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # Select specific data points
        data = {
            'Symbol': symbol,
            'Price': info.get('currentPrice', 'N/A'),
            'Market Cap': info.get('marketCap', 'N/A'),
            'PE Ratio': info.get('trailingPE', 'N/A'),
            'Dividend Yield': info.get('dividendYield', 'N/A'),
            '52 Week High': info.get('fiftyTwoWeekHigh', 'N/A'),
            '52 Week Low': info.get('fiftyTwoWeekLow', 'N/A')
        }
        return data
    except Exception as e:
        print(f"Error fetching data for {symbol}: {str(e)}")
        return None

# List of symbols
symbols = ['FIDU', 'qqq', 'brk-b']  # Add your 10 symbols here

all_data = []

for symbol in symbols:
    print(f"\nFetching data for {symbol}:")
    data = get_stock_info(symbol)
    if data:
        for key, value in data.items():
            print(f"{key}: {value}")
        all_data.append(data)
    else:
        print(f"Failed to fetch data for {symbol}")
    
    # Be nice to the server: wait a bit between requests
    time.sleep(2)

# Convert to DataFrame and save to CSV
if all_data:
    df = pd.DataFrame(all_data)
    df.to_csv('stock_data.csv', index=False)
    print("\nData saved to stock_data.csv")
else:
    print("No data was successfully fetched.")












