import json

def extract_etf_metrics(data):
    attributes = data['data'][0]['attributes']
    
    important_metrics = {
        "Name": attributes.get('name'),
        "Company Name": attributes.get('companyName'),
        "Exchange": attributes.get('exchange'),
        "Currency": attributes.get('currency'),
        "Average 3-Month Volume": attributes.get('avg3vol'),
        "Beta (60-month)": attributes.get('beta60'),
        "Book Value": attributes.get('bookValue'),
        "Cash": attributes.get('cash'),
        "Current Ratio": attributes.get('curRatio'),
        "6-Month Change %": attributes.get('chgp6m'),
        "9-Month Change %": attributes.get('chgp9m'),
        "Description": attributes.get('busDesc'),
        "Expense Ratio": attributes.get('expenseRatio'),
        "AUM": attributes.get('aum'),
        "Dividend Yield": attributes.get('divYield'),
        "P/E Ratio": attributes.get('pe'),
        "52-Week High": attributes.get('high52w'),
        "52-Week Low": attributes.get('low52w'),
        "Revenue Growth": attributes.get('revenueGrowth'),
        "Revenue Growth 3yr": attributes.get('revenueGrowth3'),
        "Return on Assets": attributes.get ('roa'),
        "Return on Equity": attributes.get ('roe')   
    }
    
    return important_metrics

# Open and read the existing 'etf_data.json' file
try:
    with open('etf_data.json', 'r') as file:
        json_data = json.load(file)
except FileNotFoundError:
    print("Error: 'etf_data.json' file not found.")
    exit(1)
except json.JSONDecodeError:
    print("Error: 'etf_data.json' contains invalid JSON.")
    exit(1)

# Extract the metrics
etf_metrics = extract_etf_metrics(json_data)

# Print the extracted metrics
print("\nExtracted ETF Metrics:")
for key, value in etf_metrics.items():
    print(f"{key}: {value}")
