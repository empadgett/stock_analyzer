import pandas as pd

# Read the existing CSV file
df = pd.read_csv('Positions')
print (df.head())
# Define the substrings to exclude
exclude_substrings = ["SPAXX", "FCFZZ", "CORE","FDRXX", "FZFXX","Pending"]

# Normalize the symbols by stripping spaces
df['Symbol'] = df['Symbol'].str.strip()

# Replace 'BRKB' with 'BRK-B'
df['Symbol'] = df['Symbol'].replace('BRKB', 'BRK-B')

# Filter the DataFrame to exclude symbols that contain any of the specified substrings
filtered_df = df[
    df['Symbol'].fillna('')  # Replace NaN with empty string
    .str.strip()  # Remove any whitespace
    .astype(str)  # Convert all values to string
    .apply(lambda x: x != '' and not any(substr in x for substr in exclude_substrings))
]


# Save the filtered DataFrame to a new CSV file
filtered_df['Symbol'].to_csv('portfoliotickers.csv', index=False)

print("Filtered symbols have been saved to portfoliotickers.csv.")






