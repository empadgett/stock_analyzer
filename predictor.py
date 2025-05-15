import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout
from datetime import datetime, timedelta
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Get data with longer history
ticker = 'msft'
end_date = datetime.now()
start_date = end_date - timedelta(days=1500)  # More historical data
data = yf.download(ticker, start=start_date, end=end_date)

# Calculate basic features
df = data.copy()
df['Returns'] = df['Close'].pct_change()
df['Volatility'] = df['Returns'].rolling(window=21).std()
df['MA10'] = df['Close'].rolling(window=10).mean()
df['MA20'] = df['Close'].rolling(window=20).mean()
df['MA50'] = df['Close'].rolling(window=50).mean()

# Momentum indicators
df['RSI'] = df['Returns'].rolling(window=14).apply(lambda x: 100 - (100 / (1 + (x[x > 0].mean() / -x[x < 0].mean()))))
df['Price_to_MA50'] = df['Close'] / df['MA50']

# Volume indicators
df['Volume_MA20'] = df['Volume'].rolling(window=20).mean()
df['Volume_Ratio'] = df['Volume'] / df['Volume_MA20']

# Remove extreme outliers
df = df[df['Returns'].abs() < df['Returns'].std() * 3]

# Select features
features = ['Close', 'Volume_Ratio', 'RSI', 'Price_to_MA50', 'Volatility']
df = df[features].dropna()

# Scale data
scaler = MinMaxScaler()
scaled_data = scaler.fit_transform(df)

# Create sequences
def create_sequences(data, seq_length):
    X, y = [], []
    for i in range(seq_length, len(data)):
        X.append(data[i-seq_length:i])
        y.append(data[i, 0])
    return np.array(X), np.array(y)

sequence_length = 21  # One month of trading days
X, y = create_sequences(scaled_data, sequence_length)

# Time-based split (more recent data for testing)
train_size = int(len(X) * 0.7)
val_size = int(len(X) * 0.15)

X_train = X[:train_size]
y_train = y[:train_size]
X_val = X[train_size:train_size+val_size]
y_val = y[train_size:train_size+val_size]
X_test = X[train_size+val_size:]
y_test = y[train_size+val_size:]

# Simpler model architecture
model = Sequential([
    LSTM(32, input_shape=(sequence_length, len(features)), return_sequences=True),
    Dropout(0.1),
    LSTM(16),
    Dropout(0.1),
    Dense(1)
])

# Compile with Huber loss
model.compile(optimizer='adam', loss='huber', metrics=['mae'])

# Callbacks
from keras.callbacks import EarlyStopping, ReduceLROnPlateau

early_stopping = EarlyStopping(
    monitor='val_loss',
    patience=10,
    restore_best_weights=True
)

lr_scheduler = ReduceLROnPlateau(
    monitor='val_loss',
    factor=0.5,
    patience=5,
    min_lr=0.0001
)

# Train with smaller batch size
history = model.fit(
    X_train, y_train,
    validation_data=(X_val, y_val),
    epochs=100,
    batch_size=32,
    callbacks=[early_stopping, lr_scheduler],
    verbose=1
)

# Rest of the code remains the same for predictions and plotting



# Make predictions and calculate metrics (same as before)
test_predictions = model.predict(X_test)

# Scale predictions back
pred_matrix = np.zeros((len(test_predictions), len(features)))
pred_matrix[:, 0] = test_predictions.flatten()
test_predictions = scaler.inverse_transform(pred_matrix)[:, 0]

actual_matrix = np.zeros((len(y_test), len(features)))
actual_matrix[:, 0] = y_test
actual_prices = scaler.inverse_transform(actual_matrix)[:, 0]

# Calculate metrics
mse = mean_squared_error(actual_prices, test_predictions)
rmse = np.sqrt(mse)
mae = mean_absolute_error(actual_prices, test_predictions)
r2 = r2_score(actual_prices, test_predictions)
mape = np.mean(np.abs((actual_prices - test_predictions) / actual_prices)) * 100

print("\nModel Performance Metrics on Test Set:")
print(f"Root Mean Squared Error: ${rmse:.2f}")
print(f"Mean Absolute Error: ${mae:.2f}")
print(f"R-squared Score: {r2:.4f}")
print(f"Mean Absolute Percentage Error: {mape:.2f}%")

# Future predictions with continuity fix
future_days = 30
last_sequence = scaled_data[-sequence_length:]
future_predictions = []
last_actual_price = df['Close'].iloc[-1]

# First prediction
current_sequence = last_sequence.reshape((1, sequence_length, len(features)))
next_pred = model.predict(current_sequence)
pred_matrix = np.zeros((1, len(features)))
pred_matrix[0, 0] = next_pred[0, 0]
first_pred_unscaled = scaler.inverse_transform(pred_matrix)[0, 0]
scaling_factor = last_actual_price / first_pred_unscaled

# Generate future predictions
for _ in range(future_days):
    current_sequence = last_sequence.reshape((1, sequence_length, len(features)))
    next_pred = model.predict(current_sequence)
    new_row = np.zeros(len(features))
    new_row[0] = next_pred[0, 0]
    new_row[1:] = last_sequence[-1, 1:]
    future_predictions.append(next_pred[0, 0])
    last_sequence = np.vstack((last_sequence[1:], new_row))

# Scale and adjust predictions
future_pred_matrix = np.zeros((len(future_predictions), len(features)))
future_pred_matrix[:, 0] = future_predictions
future_predictions = scaler.inverse_transform(future_pred_matrix)[:, 0]
future_predictions = future_predictions * scaling_factor


future_dates = pd.date_range(start=df.index[-1] + timedelta(days=1), periods=future_days, freq='B')

# Plot results
plt.figure(figsize=(15, 7))
plt.plot(df.index[-100:], df['Close'].values[-100:], label='Historical Prices')
plt.plot(future_dates, future_predictions, label='Future Predictions', color='red')  # Fixed line
plt.title(f'{ticker} Stock Price Prediction - Next {future_days} Days')
plt.legend()
plt.grid(True)
plt.show()

print(f"\nLast actual price: ${last_actual_price:.2f}")
print(f"First prediction: ${future_predictions[0]:.2f}")