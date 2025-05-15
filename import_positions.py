import pandas as pd
import yfinance as yf
import time
import pandas as pd

# Specify the path to your CSV file
file_path = 'Positions.csv'

# Read the CSV file into a pandas DataFrame
df = pd.read_csv(file_path)

# Rename the columns first
df = df.rename(columns={
    "Account Number": "account",
    "Symbol": "symbol",
    "Account Name": "account_name",
    "Description": "desc",
    "Quantity": "qty",
    "Last Price": "last_price",
    "Last Price Change": "price_change",
    "Current Value": "value",
    "Today's Gain/Loss Dollar": "today_gl_dollar",
    "Today's Gain/Loss Percent": "today_gl_percent",
    "Total Gain/Loss Dollar": "total_gl_dollar",
    "Total Gain/Loss Percent": "total_gl_percent",
    "Percent Of Account": "pct_of_account",
    "Cost Basis Total": "cost_basis",
    "Average Cost Basis": "avg_cost",
    "Type": "type"
})

# Now set the multi-index
df.set_index(['account', 'symbol'], inplace=True)
df.sort_index(inplace=True)

# Drop unused columns
columns_to_drop = ['last_price', 'price_change', 'today_gl_dollar', 'today_gl_percent', 'total_gl_dollar', 'total_gl_percent']
df = df.drop(columns=columns_to_drop)

##############################################################################
#strip info 
mask = df.index.get_level_values('account').str.contains('X69665420', case=False, na=False)
df.loc[mask, 'type'] = 'Checking'

df['type'] = df['type'].fillna('Eqty')

# Create a mask for 'Pending' in the symbol column (assuming it's the second level of the index)
pending_mask = df.index.get_level_values('symbol').astype(str).str.contains('Pending', case=False, na=False)

# Initialize the 'pending' column with 0
df['pending'] = 0

# Convert the 'value' column to numeric, removing the dollar sign and handling commas
df['value'] = df['value'].str.replace('$', '', regex=False).str.replace(',', '', regex=False).astype(float)

# Convert the 'cost_basis' column to numeric, removing the dollar sign and handling commas
df['cost_basis'] = df['cost_basis'].str.replace('$', '', regex=False).str.replace(',', '', regex=False).astype(float)

# Convert the 'avg_cost' column to numeric, removing the dollar sign and handling commas
df['avg_cost'] = df['avg_cost'].str.replace('$', '', regex=False).str.replace(',', '', regex=False).astype(float)

# Convert the 'pct_of_account' column to numeric, removing the dollar sign and handling commas
df['pct_of_account'] = df['pct_of_account'].str.replace('%', '', regex=False).str.replace(',', '', regex=False).astype(float)

# Group by account number and sum the pending amounts
pending_by_account = df.loc[pending_mask].groupby(level='account')['value'].sum()

# Iterate through accounts with pending amounts and update the 'pending' column
for account, amount in pending_by_account.items():
    df.loc[df.index.get_level_values('account') == account, 'pending'] = amount

# Remove rows with 'Pending' in the symbol
df = df.loc[~pending_mask]

#identify Bonds
mask = df['desc'].astype(str).str.contains('bond', case=False, na=False)
df.loc[mask, 'type'] = 'Bond'
#identify Cash
mask = (df['desc'].astype(str).str.contains('DEPOSIT SWEEP|MONEY MARKET|CASH RESERVES', case=False, na=False) & 
        (df['type'] != 'Checking'))
df.loc[mask, 'type'] = 'Cash'

date_downloaded = df.index[df.index.get_level_values(0).str.contains('Date downloaded', case=False, na=False)][0][0]
df['date']=date_downloaded

first_index_column = df.index.get_level_values(0).unique()

df_equity = df[df['type'] == 'Eqty']
df['date']=date_downloaded

lines_to_remove = [
    "Brokerage services are provided by Fidelity Brokerage Services LLC (FBS), 900 Salem Street, Smithf",
    "Date downloaded",
    "The data and informati" 
]

# Function to check if a string starts with any of the specified lines
def starts_with_any(string, prefixes):
    return any(string.startswith(prefix) for prefix in prefixes)

# Remove the specified lines from the index
df = df[~df.index.get_level_values(0).astype(str).map(lambda x: starts_with_any(x, lines_to_remove))]

#Create a set of unique 'Eqty' symbols
df_equity = df_equity.reset_index(level='symbol', drop=False)
df_equity = df_equity.dropna(subset=['symbol'])
df_equity = df_equity.set_index('symbol', append=True)
second_index_column = df_equity.index.get_level_values('symbol').unique()

# Convert second_index_column to a set
symbol_set = set(second_index_column)

# Create the .env.symbols file and write the set contents
with open('.env.symbols', 'w') as f:
    f.write(f"SYMBOLS={','.join(symbol_set)}\n")


# Sort the index
df.sort_index(inplace=True)

print('Fundamentals have been fetched.')

df.to_csv('post_positions.csv')

print (df)
       


