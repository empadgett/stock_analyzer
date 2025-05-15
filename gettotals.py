import pandas as pd
df=pd.read_csv('post_positions.csv')

totals_df= pd.DataFrame()
temp_df=df

# Remove the dollar sign and convert column 'b' to numeric
temp_df['value'] = temp_df['value'].str.replace('$', '', regex=False).astype(float)

# Convert column 'b' to numeric
temp_df['value'] = pd.to_numeric(df['value'])

result = df.groupby(['account','type'])['value'].sum().reset_index()


# Calculate total for each account
result['total'] = result.groupby('account')['value'].transform('sum')

# Calculate the ratio for each type and add it to the 'pcnt' column
result['pcnt'] = result['value'] / result['total']*100.0

# Extract the full timestamp from the 'account' cell that contains 'Date downloaded'
result['data-date'] = result['account'].apply(lambda x: x if 'Date downloaded' in x else None)

# Fill the 'data-date' column with the extracted timestamp for all rows
timestamp = result['data-date'].dropna().iloc[0] if not result['data-date'].dropna().empty else None
result['data-date'] = timestamp
# Remove rows where 'account' contains 'Date downloaded'
result = result[~result['account'].str.contains('Date downloaded', na=False)]

result.reset_index()
result['total-cash'] = result['total'] *0.9



result['target'] = 0
result['total-total']=0
#result['eqty-target'] = 0
total_sum = result['value'].sum()
# Set all cells in 'total-total' column to the total sum
result['total-total'] = total_sum
# Iterate through each row in the DataFrame
for index, row in result.iterrows():
    if row['type'] == 'Cash':
        result.at[index, 'target'] = row['total'] * 0.1
        result.at[index, 'target%'] = 10.0
    elif row['type'] == 'Bond':
        result.at[index, 'target'] = row['total'] * 0.5
        result.at[index, 'target%'] = 50.0
    elif row['type'] == 'Eqty':
        result.at[index, 'target'] = row['total'] * 0.5
        result.at[index, 'target%'] = 50.0
        
# Calculate the total of the 'total' column

        
print(result)

result.to_csv('position_ratios.csv')