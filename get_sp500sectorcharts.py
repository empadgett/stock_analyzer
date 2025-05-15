import pandas as pd
import matplotlib.pyplot as plt
import os

# Directory containing the CSV files
directory = 'sp500sectorpricedata'

# Initialize a DataFrame to hold performance data
performance_data = []

# Initialize a plot
plt.figure(figsize=(12, 6))

# Loop through all files in the directory
for filename in os.listdir(directory):
    if filename.endswith('.csv'):
        # Construct full file path
        file_path = os.path.join(directory, filename)

        # Read the CSV file
        data = pd.read_csv(file_path)

        # Convert 'Date' column to datetime format
        data['Date'] = pd.to_datetime(data['Date'])

        # Calculate 20-day performance
        if len(data) >= 20:
            last_20_days = data['Close'][-20:]
            performance_20_days = (last_20_days.iloc[-1] - last_20_days.iloc[0]) / last_20_days.iloc[0] * 100
        else:
            performance_20_days = None

        # Calculate YTD performance
        ytd_data = data[data['Date'] >= pd.to_datetime(f'{data["Date"].dt.year.iloc[0]}-01-01')]
        if not ytd_data.empty:
            performance_ytd = (ytd_data['Close'].iloc[-1] - ytd_data['Close'].iloc[0]) / ytd_data['Close'].iloc[0] * 100
        else:
            performance_ytd = None

        # Get the description from the DataFrame and clean it
        description = data['Description'].iloc[0].replace('SPDR Select Sector Fund - ', '')  # Clean description

        # Append the performance metrics to the list
        performance_data.append({
            'Sector': filename[:-4],  # Remove '.csv' from filename
            'Description': description,
            '20-Day Performance (%)': performance_20_days,
            'YTD Performance (%)': performance_ytd
        })

        # Normalize the Closing price for plotting
        normalized_close = (data['Close'] - data['Close'].min()) / (data['Close'].max() - data['Close'].min())

        # Plot the normalized Closing price with cleaned description in the label
        plt.plot(data['Date'], normalized_close, label=f"{filename[:-4]} ({description})")  # Remove '.csv' from filename for the label

# Create a DataFrame from the performance data
performance_df = pd.DataFrame(performance_data)

# Display the DataFrame
print(performance_df)

# Customize the plot
plt.title('Normalized Closing Prices of S&P 500 Sectors')
plt.xlabel('Date')
plt.ylabel('Normalized Closing Price')
plt.legend()
plt.grid()
plt.xticks(rotation=45)
plt.tight_layout()

# Show the plot
plt.show()








