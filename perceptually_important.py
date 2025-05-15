import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf

def find_pips(data: np.array, n_pips: int, dist_measure: int):
    pips_x = [0, len(data) - 1]  # Index
    pips_y = [data[0], data[-1]]  # Price

    for curr_point in range(2, n_pips):
        md = 0.0  # Max distance
        md_i = -1  # Max distance index
        insert_index = -1

        for k in range(0, curr_point - 1):
            left_adj = k
            right_adj = k + 1

            time_diff = pips_x[right_adj] - pips_x[left_adj]
            price_diff = pips_y[right_adj] - pips_y[left_adj]
            slope = price_diff / time_diff
            intercept = pips_y[left_adj] - pips_x[left_adj] * slope

            for i in range(pips_x[left_adj] + 1, pips_x[right_adj]):
                d = 0.0  # Distance
                if dist_measure == 1:  # Euclidean distance
                    d = ((pips_x[left_adj] - i) ** 2 + (pips_y[left_adj] - data[i]) ** 2) ** 0.5
                    d += ((pips_x[right_adj] - i) ** 2 + (pips_y[right_adj] - data[i]) ** 2) ** 0.5
                elif dist_measure == 2:  # Perpendicular distance
                    d = abs((slope * i + intercept) - data[i]) / ((slope ** 2 + 1) ** 0.5)
                else:  # Vertical distance    
                    d = abs((slope * i + intercept) - data[i])

                if d > md:
                    md = d
                    md_i = i
                    insert_index = right_adj

        pips_x.insert(insert_index, md_i)
        pips_y.insert(insert_index, data[md_i])

    return pips_x, pips_y

ticker = 'TSLA'  # Change to AAPL
data = yf.download(ticker, start='2024-01-01', end='2024-10-12')

if __name__ == "__main__":
    data['Date'] = data.index.astype('datetime64[s]')
    data = data.set_index('Date')

    # Check if enough data is available
    if len(data) < 40:
        raise ValueError("Not enough data points to extract the specified range.")

    # Adjust index i to be within the bounds of the data length
    max_index = len(data)
    i = min(max_index - 1, 1198)  # Ensure i does not exceed the length of data

    if i < 40:
        raise IndexError("Index i is too low to extract the specified range.")

    x = data['Close'].iloc[i-40:i].to_numpy()  # Use 'Close' column
    pips_x, pips_y = find_pips(x, 5, 2)

    pd.Series(x).plot()
    for j in range(5):
        plt.plot(pips_x[j], pips_y[j], marker='o', color='red')

    plt.title(f'{ticker} Price with Detected Pips')
    plt.xlabel('Days')
    plt.ylabel('Price')
    plt.show()
