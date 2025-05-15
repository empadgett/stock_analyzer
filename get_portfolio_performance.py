import pandas as pd
import os
import ta

def calculate_volatility(df):
    # Calculate daily returns
    df['Returns'] = df['Close'].pct_change()
    # Calculate the standard deviation of daily returns
    volatility = df['Returns'].std()
    # Annualize the volatility (assuming 252 trading days in a year)
    annualized_volatility = volatility * (252 ** 0.5)
    return annualized_volatility, volatility

def calculate_weekly_performance(df):
    """Calculate weekly performance as a percentage."""
    weekly_data = df.resample('W-Mon').last()  # Resample to weekly frequency
    weekly_returns = weekly_data['Close'].pct_change() * 100  # Calculate percentage change
    
    # Calculate percentage change
    weekly_change = ((df['Close'].iloc[-1] - df['Open'].iloc[-6]) / df['Open'].iloc[-6]) * 100

    # Round the result
    weekly_change = round(weekly_change, 2)
    weekly_returns = weekly_change
    
    
    return weekly_returns



def get_trend_strength(current_price, sma20, sma50, sma200):
    """Calculate trend strength based on price and moving averages."""
    strength = 0
    if current_price > sma20:
        strength += 1
    if current_price > sma50:
        strength += 1
    if current_price > sma200:
        strength += 2
    if sma20 > sma50:
        strength += 1
    if sma50 > sma200:
        strength += 2
    pct_from_200 = ((current_price - sma200) / sma200) * 100
    if pct_from_200 > 20:
        strength += 1
    elif pct_from_200 < -20:
        strength -= 1
    return strength 

def calculate_relative_strength(asset_returns, spy_returns):
    """Calculate relative strength against SPY."""
    return asset_returns.mean() - spy_returns.mean()

def analyze_conditions(current_price, sma20, sma50, sma200, pct_from_20sma, pct_from_50sma):
    """Analyze technical conditions based on moving averages."""
    conditions = []
    if pct_from_20sma > 5 and pct_from_50sma > 3:
        conditions.append("Potential Breakout")
    if pct_from_20sma < -5 and pct_from_50sma < -3:
        conditions.append("Potential Breakdown")
    if pct_from_20sma > 10:
        conditions.append("Overbought")
    if pct_from_20sma < -10:
        conditions.append("Oversold")
    if sma20 > sma50 > sma200:
        conditions.append("Strong Uptrend")
    if sma20 < sma50 < sma200:
        conditions.append("Strong Downtrend")
    return conditions


# Directory containing the portfolio price data
directory = 'portfoliopricedata'

# Initialize a variable to hold SPY data
spy_data = None

# Initialize a list to hold results for the table
results = []

# First pass to find SPY data
for filename in os.listdir(directory):
    if filename.endswith('.csv') and 'SPY' in filename:
        spy_data = pd.read_csv(os.path.join(directory, filename), parse_dates=['Date'], index_col='Date')
        spy_data['Returns'] = spy_data['Close'].pct_change()
        break

if spy_data is None:
    print("SPY data not found. Please ensure it is in the directory.")
else:
    # Calculate SPY metrics
    spy_volatility, _ = calculate_volatility(spy_data)
    average_daily_return_spy = spy_data['Returns'].mean()
    annualized_return_spy = (1 + average_daily_return_spy) ** 252 - 1
    previous_30_day_return_spy = (spy_data['Close'].iloc[-1] / spy_data['Close'].iloc[-31]) - 1 if len(spy_data) >= 30 else None

    # Calculate weekly performance for SPY
    spy_weekly_returns = calculate_weekly_performance(spy_data)

    # Calculate SMAs
    sma20 = ta.trend.sma_indicator(spy_data['Close'], window=20).iloc[-1]
    sma50 = ta.trend.sma_indicator(spy_data['Close'], window=50).iloc[-1]
    sma200 = ta.trend.sma_indicator(spy_data['Close'], window=200).iloc[-1]
    current_price = spy_data['Close'].iloc[-1]

    pct_from_20sma = ((current_price - sma20) / sma20) * 100
    pct_from_50sma = ((current_price - sma50) / sma50) * 100
    pct_from_200sma = ((current_price - sma200) / sma200) * 100

    trend = get_trend_strength(current_price, sma20, sma50, sma200)
    conditions = analyze_conditions(current_price, sma20, sma50, sma200, pct_from_20sma, pct_from_50sma)

    results.append({
        'Filename': 'SPY',
        'Annualized Volatility': f"{spy_volatility:.4f}",
        '1 Mo Return': f"{previous_30_day_return_spy * 100:.1f}%" if previous_30_day_return_spy is not None else "Not enough data",
        'Annualized Return': f"{annualized_return_spy * 100:.1f}%",
        'Beta (SPY)': "1.0000",
        '20SMA': f"${sma20:.2f} ({pct_from_20sma:.1f}%)",
        '50SMA': f"${sma50:.2f} ({pct_from_50sma:.1f}%)",
        '200SMA': f"${sma200:.2f} ({pct_from_200sma:.1f}%)",
        'Trend': trend,
        'Price': f"${current_price:.2f}",
        'Technical Conditions': ', '.join(conditions) if conditions else "Normal Trading Range",
        'Weekly Performance': f"{spy_weekly_returns.mean():.2f}%"  # Average weekly performance
    })

    # Second pass for other files
    for filename in os.listdir(directory):
        if filename.endswith('.csv') and 'SPY' not in filename:
            df = pd.read_csv(os.path.join(directory, filename), parse_dates=['Date'], index_col='Date')
            df['Returns'] = df['Close'].pct_change().dropna()
            df.dropna(inplace=True)

            annualized_volatility, volatility = calculate_volatility(df)
            average_daily_return = df['Returns'].mean()
            annualized_return = (1 + average_daily_return) ** 252 - 1
            previous_30_day_return = (df['Close'].iloc[-1] / df['Close'].iloc[-31]) - 1 if len(df) >= 30 else None

            # Calculate weekly performance for the asset
            asset_weekly_returns = calculate_weekly_performance(df)

            combined_returns = pd.concat([df['Returns'], spy_data['Returns']], axis=1).dropna()
            combined_returns.columns = ['Sector', 'SPY']
            covariance = combined_returns.cov().iloc[0, 1]
            market_variance = combined_returns['SPY'].var()
            beta = covariance / market_variance if market_variance != 0 else None
            relative_strength= annualized_return / annualized_return_spy - 1
            
            # Calculate SMAs
            sma20 = ta.trend.sma_indicator(df['Close'], window=20).iloc[-1]
            sma50 = ta.trend.sma_indicator(df['Close'], window=50).iloc[-1]
            sma200 = ta.trend.sma_indicator(df['Close'], window=200).iloc[-1]
            current_price = df['Close'].iloc[-1]

            pct_from_20sma = ((current_price - sma20) / sma20) * 100
            pct_from_50sma = ((current_price - sma50) / sma50) * 100
            pct_from_200sma = ((current_price - sma200) / sma200) * 100

            trend = get_trend_strength(current_price, sma20, sma50, sma200)
            conditions = analyze_conditions(current_price, sma20, sma50, sma200, pct_from_20sma, pct_from_50sma)


            # Append results to the list
            results.append({
                'Filename': filename,
                'Annualized Volatility': f"{annualized_volatility:.4f}",
                '1 Mo Return': f"{previous_30_day_return * 100:.1f}%" if previous_30_day_return is not None else "Not enough data",
                'Annualized Return': f"{annualized_return * 100:.1f}%",
                'Beta (SPY)': f"{beta:.4f}" if beta is not None else "Not enough data",
                '20SMA': f"${sma20:.2f}",
                'PCT From 20SMA': f"{pct_from_20sma:.1f}%",
                '50SMA': f"${sma50:.2f}",
                'PCT From 50SMA': f"{pct_from_50sma:.1f}%",
                '200SMA': f"${sma200:.2f}",
                'PCT From 200SMA': f"{pct_from_200sma:.1f}%",
                'Trend': trend,
                'Price': f"${current_price:.2f}",
                'Technical Conditions': ', '.join(conditions) if conditions else "Normal Trading Range",
                'Weekly Performance': f"{asset_weekly_returns.mean():.2f}%",  # Average weekly performance
                'Relative Strength to SPY': f"{relative_strength:.2f}%"  # Relative strength
            })

    # Create a DataFrame from the results
    results_df = pd.DataFrame(results)

from rich.console import Console
from rich.table import Table
console = Console()
console.clear()
console.print(results_df)

import os
from datetime import datetime
import pandas as pd
from tabulate import tabulate  # pip install tabulate

# Create timestamp for filename
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_dir = 'reports'

# Create reports directory if it doesn't exist
if not os.path.exists(output_dir):
    os.makedirs(output_dir)


# Rename 'Filename' to 'Ticker' and strip '.csv'
results_df['Ticker'] = results_df['Filename'].str.replace('.csv', '', regex=False)
results_df.drop(columns=['Filename'], inplace=True)

# 1. Save as CSV
csv_file = f'{output_dir}/stock_analysis.csv'  # Remove timestamp for single version
results_df.to_csv(csv_file, index=False)

# 2. Save as Excel with formatting
# Convert all relevant columns to numeric types, ignoring non-numeric columns
results_df['1 Mo Return'] = pd.to_numeric(results_df['1 Mo Return'].str.replace('%', '').str.replace(' ', ''), errors='coerce')
results_df['Annualized Return'] = pd.to_numeric(results_df['Annualized Return'].str.replace('%', '').str.replace(' ', ''), errors='coerce')
results_df['Beta (SPY)'] = pd.to_numeric(results_df['Beta (SPY)'], errors='coerce')
results_df['20SMA'] = pd.to_numeric(results_df['20SMA'].str.replace('$', ''), errors='coerce')
results_df['PCT From 20SMA'] = pd.to_numeric(results_df['PCT From 20SMA'].str.replace('%', '').str.replace(' ', ''), errors='coerce')
results_df['50SMA'] = pd.to_numeric(results_df['50SMA'].str.replace('$', ''), errors='coerce')
results_df['PCT From 50SMA'] = pd.to_numeric(results_df['PCT From 50SMA'].str.replace('%', '').str.replace(' ', ''), errors='coerce')
results_df['200SMA'] = pd.to_numeric(results_df['200SMA'].str.replace('$', ''), errors='coerce')
results_df['PCT From 200SMA'] = pd.to_numeric(results_df['PCT From 200SMA'].str.replace('%', '').str.replace(' ', ''), errors='coerce')
results_df['Price'] = pd.to_numeric(results_df['Price'].str.replace('$', '').str.replace(' ', ''), errors='coerce')
results_df['Weekly Performance'] = pd.to_numeric(results_df['Weekly Performance'].str.replace('%', '').str.replace(' ', ''), errors='coerce')
results_df['Relative Strength to SPY'] = pd.to_numeric(results_df['Relative Strength to SPY'].str.replace('%', '').str.replace(' ', ''), errors='coerce')
results_df['Trend'] = pd.to_numeric(results_df['Trend'], errors='coerce')
results_df['Ticker'] = results_df['Ticker'].astype(str)  # Keep Ticker as string

excel_file = f'{output_dir}/stock_analysis.xlsx'  # Main save location
with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
    results_df.to_excel(writer, sheet_name='Stock Analysis', index=False)
    workbook = writer.book
    worksheet = writer.sheets['Stock Analysis']
    
    # Add formatting
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#D3D3D3',
        'border': 1
    })
    
    # Format header row
    for col_num, value in enumerate(results_df.columns.values):
        worksheet.write(0, col_num, value, header_format)

    # Auto resize columns based on their content
    for col_num in range(len(results_df.columns)):
        max_length = max(
            results_df.iloc[:, col_num].astype(str).map(len).max(),  # Maximum length of data in the column
            len(results_df.columns[col_num])  # Length of the header
        )
        worksheet.set_column(col_num, col_num, max_length + 2)  # Add some padding

# Save a copy to the specified location
desktop_excel_file = '/mnt/c/tmp/stock_analysis.xlsx'  # Adjusted for WSL

# Create the directory if it doesn't exist
os.makedirs(os.path.dirname(desktop_excel_file), exist_ok=True)

# Check if the file will be saved
print(f"Attempting to save a copy to: {desktop_excel_file}")

# Save the DataFrame to the specified location
try:
    results_df.to_excel(desktop_excel_file, index=False)
    print("Excel file save command executed.")
except Exception as e:
    print(f"Failed to save the copy. Error: {e}")



# 3. Save as formatted text file
txt_file = f'{output_dir}/stock_analysis.txt'  # Remove timestamp for single version
with open(txt_file, 'w') as f:
    # Write header
    f.write(f"Stock Analysis Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("=" * 100 + "\n\n")
    
    # Write table using tabulate
    f.write(tabulate(results_df, headers='keys', tablefmt='grid'))
    
    # Write footer
    f.write(f"\n\nTotal stocks analyzed: {len(results_df)}\n")
    f.write(f"Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 4. Save as HTML
html_file = f'{output_dir}/stock_analysis.html'  # Remove timestamp for single version
html_content = f"""
<html>
<head>
    <title>Stock Analysis Report</title>
    <style>
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ padding: 8px; text-align: left; border: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        tr:hover {{ background-color: #f5f5f5; }}
    </style>
</head>
<body>
    <h2>Stock Analysis Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</h2>
    {results_df.to_html(index=False)}
    <p>Total stocks analyzed: {len(results_df)}</p>
</body>
</html>
"""
with open(html_file, 'w') as f:
    f.write(html_content)

print(f"\nReports saved in {output_dir}:")
print(f"1. CSV: {csv_file}")
print(f"2. Excel: {excel_file}")
print(f"3. Text: {txt_file}")
print(f"4. HTML: {html_file}")








