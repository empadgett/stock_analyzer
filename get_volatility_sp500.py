import pandas as pd
import os

def calculate_volatility(df):
    # Calculate daily returns
    df['Returns'] = df['Close'].pct_change()
    priceperf=df['Close'].pct_change()
    # Calculate the standard deviation of daily returns
    volatility = df['Returns'].std()
    # Annualize the volatility (assuming 252 trading days in a year)
    annualized_volatility = volatility * (252 ** 0.5)
    return annualized_volatility, volatility,priceperf

# Directory containing the sp500 price data
directory = 'sp500sectorpricedata'

# Initialize a variable to hold SPY data
spy_data = None

# First pass to find SPY data
for filename in os.listdir(directory):
    if filename.endswith('.csv'):  # Check if the file is a CSV
        file_path = os.path.join(directory, filename)  # Get full file path
        if 'SPY' in filename:
            spy_data = pd.read_csv(file_path)  # Store SPY data for beta calculation
            spy_data['Returns'] = spy_data['Close'].pct_change()  # Calculate returns for SPY
            break  # Exit the loop once SPY data is found

# If SPY data was not found, print an error and exit
if spy_data is None:
    print("SPY data not found. Please ensure it is in the directory.")
else:
    # Second pass to process other files
    directory = 'sp500pricedata'
    for filename in os.listdir(directory):
        if filename.endswith('.csv') and 'SPY' not in filename:  # Exclude SPY file
            file_path = os.path.join(directory, filename)  # Get full file path
            df = pd.read_csv(file_path)  # Read the CSV file into a DataFrame
            df.reset_index(inplace=True)

            # Calculate volatility
            annualized_volatility, volatility,priceperf = calculate_volatility(df)

            # Calculate beta
            combined_returns = pd.concat([df['Returns'], spy_data['Returns']], axis=1).dropna()
            combined_returns.columns = ['Sector', 'SPY']

            covariance = combined_returns.cov().iloc[0, 1]
            market_variance = combined_returns['SPY'].var()
            beta = covariance / market_variance
            
            # Print results
            if not df['Close'].empty:
                start_price = df['Close'].iloc[0]
                end_price = df['Close'].iloc[-1]
                percent_change = ((end_price - start_price) / start_price) * 100
                
                # Print results if percent price change is greater than 20%
                if percent_change > 90:
                    print(f"Filename: {filename}")
                    print(f"Percent Price Change: {percent_change:.2f}%")
                    print(f"Daily Volatility: {volatility:.4f}")
                    print(f"Annualized Volatility: {annualized_volatility:.4f}")
                    print(f"Beta: {beta:.4f}")
                    
                

    