import http.client
import json
import os
import time
import sys

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# Read symbols from .env.symbols
with open('.env.symbols', 'r') as f:
    symbols = [symbol.strip() for symbol in f.read().strip().split('=')[1].split(',')]

# Ensure the ticker_data directory exists
os.makedirs('ticker_data', exist_ok=True)

# Set up the connection
conn = http.client.HTTPSConnection("seeking-alpha-finance.p.rapidapi.com")

headers = {
    'x-rapidapi-key': "b30ca7c507msh7ee016d7b74c551p1e91d9jsn23469fb62b88",
    'x-rapidapi-host': "seeking-alpha-finance.p.rapidapi.com"
}

def write_to_json(symbol, json_data):
    json_file = f'ticker_data/{symbol}.json'
    with open(json_file, 'w') as f:
        json.dump(json_data, f, indent=2)
    return json_file

def check_json(file_path):
    if not os.path.exists(file_path):
        print(f"File does not exist: {file_path}")
        return False
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        if isinstance(data, dict) and len(data) <= 1 and "detail" in data:
            print(f"Error in JSON data: {data}")
            return False
        return True
    except json.JSONDecodeError as e:
        print(f"JSON decode error in {file_path}: {str(e)}")
        return False

def fetch_data(symbol):
    for attempt in range(MAX_RETRIES):
        try:
            conn.request("GET", f"/v1/symbols/data?ticker_slug={symbol.lower().replace('.', '-')}", headers=headers)
            res = conn.getresponse()
            data = res.read()
            json_data = json.loads(data.decode("utf-8"))
            
            if "detail" in json_data:
                if "General client error" in json_data["detail"] or json_data["detail"] == "Object not found":
                    print(f"Attempt {attempt + 1} for {symbol} failed. Error: {json_data['detail']}. Retrying...")
                    time.sleep(RETRY_DELAY)
                    continue
            
            return json_data
        except Exception as e:
            print(f"Error on attempt {attempt + 1} for {symbol}: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                return {"error": str(e)}
    
    return {"error": f"Failed to fetch data for {symbol} after {MAX_RETRIES} attempts"}

failed_symbols = []
fetched_symbols = []

for i, symbol in enumerate(symbols):
    json_file = f'ticker_data/{symbol}.json'
    
    if check_json(json_file):
        print(f"Valid data already exists for {symbol}. Skipping.")
        continue
    
    print(f"Fetching data for {symbol}...")
    json_data = fetch_data(symbol)
    
    if "error" in json_data:
        print(f"Failed to fetch data for {symbol}: {json_data['error']}")
        failed_symbols.append(symbol)
        continue
    
    json_file = write_to_json(symbol, json_data)
    
    if not check_json(json_file):
        print(f"Warning: The JSON file for {symbol} ({json_file}) is invalid or contains an error.")
        failed_symbols.append(symbol)
    else:
        print(f"Data for {symbol} saved successfully to {json_file}")
        fetched_symbols.append(symbol)

    # Add delay to respect rate limit (5 requests per second)
    if i < len(symbols) - 1:  # No need to wait after the last request
        time.sleep(0.2)  # 1/5 second delay

print("\nData fetching process completed.")
if fetched_symbols:
    print(f"\nFetched data for {len(fetched_symbols)} symbols: {', '.join(fetched_symbols)}")
if failed_symbols:
    print(f"\nThe following symbols failed or returned errors: {', '.join(failed_symbols)}")
print(f"\nSkipped {len(symbols) - len(fetched_symbols) - len(failed_symbols)} symbols with existing valid data.")

# Retry failed symbols
if failed_symbols:
    print("\nRetrying failed symbols...")
    for symbol in failed_symbols[:]:  # Create a copy of the list to iterate over
        print(f"Retrying {symbol}...")
        json_data = fetch_data(symbol)
        if "error" not in json_data:
            json_file = write_to_json(symbol, json_data)
            if check_json(json_file):
                print(f"Successfully fetched data for {symbol} on retry.")
                fetched_symbols.append(symbol)
                failed_symbols.remove(symbol)
            else:
                print(f"Failed to fetch valid data for {symbol} on retry.")
        else:
            print(f"Failed to fetch data for {symbol} on retry: {json_data['error']}")
        time.sleep(.5)  # Wait a second between retries

    print("\nRetry process completed.")
    if failed_symbols:
        print(f"Symbols that still failed after retry: {', '.join(failed_symbols)}")
    else:
        print("All retried symbols were successfully fetched.")
















