import http.client
import json

# Fetch data from the API
conn = http.client.HTTPSConnection("seeking-alpha-finance.p.rapidapi.com")

headers = {
    'x-rapidapi-key': "b30ca7c507msh7ee016d7b74c551p1e91d9jsn23469fb62b88",
    'x-rapidapi-host': "seeking-alpha-finance.p.rapidapi.com"
}

#conn.request("GET", "/v1/symbols/financials/fundamentals-metrics?ticker_slug=qqq&statement_type=balance-sheet&currency=ARS&period_type=annual", headers=headers)
#symbol data
#conn.request("GET", "/v1/symbols/data?ticker_slug=qqq", headers=headers)
#smbol eps and other good stuff
conn.request("GET", "/v1/symbols/ticker-data?ticker_slug=qqq", headers=headers)

res = conn.getresponse()
data = res.read()

# Parse the JSON data
json_data = json.loads(data.decode("utf-8"))

# Save the data to a file
with open('etf_data.json', 'w') as f:
    json.dump(json_data, f, indent=4)

print("Data saved to etf_data.json")










