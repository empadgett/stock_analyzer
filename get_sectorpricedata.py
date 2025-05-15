import os
import yfinance as yf
import pandas as pd

# Function to fetch stock data and simple description
def fetch_stock_data(ticker):
    try:
        # Fetch data
        stock_data = yf.download(ticker, period='ytd', interval='1d')
        
        # Check if the DataFrame is empty
        if stock_data.empty:
            print(f"No data returned for ticker: {ticker}")
            return None, None
        
        # Fetch simple symbol description
        ticker_info = yf.Ticker(ticker)
        description = ticker_info.info.get('longName','No desript available.')
        
        return stock_data, description
    
    except Exception as e:
        print(f"Error fetching data for ticker {ticker}: {e}")
        return None, None

# Read the tickers from the CSV file
df = pd.read_csv('spsectors_etf.csv')

# Directory to store CSV files
directory = 'sp500sectorpricedata'

# Create the directory if it doesn't exist
os.makedirs(directory, exist_ok=True)

# Loop through the list of tickers and fetch data
for i in range(len(df)):
    ticker = df.iloc[i]['Symbol']
    data, desc = fetch_stock_data(ticker)
    
    if data is not None:
        # Add the description as a new column
        data['Description'] = desc

        # Specify the CSV file name for the ticker
        csv_file_name = os.path.join(directory, f"{ticker}.csv")
        
        # Save the DataFrame to a CSV file
        data.to_csv(csv_file_name, index=True)

        print(f"Data for {ticker} has been saved to {csv_file_name}.")

