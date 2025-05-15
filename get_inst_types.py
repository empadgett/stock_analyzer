import requests
import pandas as pd

import time

with open('.env.symbols', 'r') as f:
    etf_positions = f.read().strip().split('=')[1].split(',')

# API headers
headers = {
    'x-rapidapi-key': "b30ca7c507msh7ee016d7b74c551p1e91d9jsn23469fb62b88",
    'x-rapidapi-host': "twelve-data1.p.rapidapi.com"
}

# Function to classify symbol
def classify_symbol(ticker):
    url = f"https://twelve-data1.p.rapidapi.com/symbol_search?symbol={ticker}&outputsize=1"
    response = requests.get(url, headers=headers)
    json_data = response.json()
    
    if 'data' in json_data and len(json_data['data']) > 0:
        asset_type = json_data['data'][0].get('instrument_type')
        return asset_type
    return "Unknown"

# List to hold symbols and their types
position_types = []

# Iterate over ETF positions and classify
for i, ticker in enumerate(etf_positions):
    asset_type = classify_symbol(ticker)
    position_types.append({'symbol': ticker, 'inst_type': asset_type})

    # Rate limiting: wait if necessary
    if (i + 1) % 8 == 0:  # After every 8 requests
        print("Rate limit reached. Sleeping for 60 seconds...")
        time.sleep(60)  # Sleep for 60 seconds

# Create a DataFrame and save to CSV
df = pd.DataFrame(position_types)
df.to_csv('position_type.csv', index=False)

print("Position types saved to position_type.csv")


