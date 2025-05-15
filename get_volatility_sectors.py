import pandas as pd
import os

def calculate_volatility(df):
    # Calculate daily returns
    df['Returns'] = df['Close'].pct_change()
    # Calculate the standard deviation of daily returns
    volatility = df['Returns'].std()
    # Annualize the volatility (assuming 252 trading days in a year)
    annualized_volatility = volatility * (252 ** 0.5)
    return annualized_volatility, volatility

# Directory containing the sector price data
directory = 'sp500sectorpricedata'

# Initialize a variable to hold SPY data
spy_data = None

# Initialize a list to hold results for the table
results = []

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
    # Calculate SPY metrics
    spy_volatility, _ = calculate_volatility(spy_data)
    average_daily_return_spy = spy_data['Returns'].mean()
    annualized_return_spy = (1 + average_daily_return_spy) ** 252 - 1
    previous_30_day_return_spy = (spy_data['Close'].iloc[-1] / spy_data['Close'].iloc[-31]) - 1 if len(spy_data) >= 30 else None

    # Append SPY results to the list
    results.append({
        'Filename': 'SPY',
        'Annualized Volatility': f"{spy_volatility:.4f}",
        '1 Mo Return': f"{previous_30_day_return_spy * 100:.1f}%" if previous_30_day_return_spy is not None else "Not enough data",
        'Annualized Return': f"{annualized_return_spy * 100:.1f}%",
        'Beta (SPY)': "1.0000"  # Beta of SPY to itself is always 1
    })

    # Second pass to process other files
    for filename in os.listdir(directory):
        if filename.endswith('.csv') and 'SPY' not in filename:  # Exclude SPY file
            file_path = os.path.join(directory, filename)  # Get full file path
            df = pd.read_csv(file_path)  # Read the CSV file into a DataFrame
            df['Returns'] = df['Close'].pct_change()  # Calculate returns assuming 'Close' column exists
            df.dropna(inplace=True)  # Drop NaN values after calculating returns

            # Calculate annualized return
            average_daily_return = df['Returns'].mean()
            annualized_return = (1 + average_daily_return) ** 252 - 1

            # Calculate previous 30-day return
            previous_30_day_return = (df['Close'].iloc[-1] / df['Close'].iloc[-31]) - 1 if len(df) >= 30 else None

            # Calculate volatility
            annualized_volatility, volatility = calculate_volatility(df)

            # Calculate beta
            combined_returns = pd.concat([df['Returns'], spy_data['Returns']], axis=1).dropna()
            combined_returns.columns = ['Sector', 'SPY']

            covariance = combined_returns.cov().iloc[0, 1]
            market_variance = combined_returns['SPY'].var()
            beta = covariance / market_variance if market_variance != 0 else None  # Prevent division by zero

            # Append results to the list
            results.append({
                'Filename': filename,
                'Annualized Volatility': f"{annualized_volatility:.4f}",
                '1 Mo Return': f"{previous_30_day_return * 100:.1f}%" if previous_30_day_return is not None else "Not enough data",
                'Annualized Return': f"{annualized_return * 100:.1f}%",
                'Beta (SPY)': f"{beta:.4f}" if beta is not None else "Not enough data"
            })

    # Create a DataFrame from the results
    results_df = pd.DataFrame(results)

    # Print the results table
    print(results_df.to_string(index=False))








