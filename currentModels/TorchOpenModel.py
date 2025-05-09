import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import DataLoader, Dataset
import matplotlib.pyplot as plt


# Define the LSTM model
class LSTMModel(nn.Module):
    def __init__(self, input_dim, hidden_dim=100, num_layers=2, dropout=0.2):
        super(LSTMModel, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, dropout=dropout, batch_first=True)
        self.fc = nn.Linear(hidden_dim, 1)

    def forward(self, x):
        batch_size = x.size(0)
        h0 = torch.zeros(self.num_layers, batch_size, self.hidden_dim, device=x.device)
        c0 = torch.zeros(self.num_layers, batch_size, self.hidden_dim, device=x.device)
        out, _ = self.lstm(x, (h0, c0))
        out = out[:, -1, :]
        out = self.fc(out)
        return out


# Load the dataset (you can replace this with your actual dataset)
data = pd.read_csv('technical_indicators.csv')

# Convert the date column to datetime if not already
data['date'] = pd.to_datetime(data['date'])

# Select relevant features (you can modify this based on your features)
features = ['Close', 'Volume', 'RSI', 'MACD', 'MACD_Signal', 'MACD_Hist', 'BB_Mid', 'BB_Upper', 'BB_Lower']
target = 'Close'  # You are predicting 'Close' price

# Scale the data (use the same scaler you used during training)
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(data[features])

# Prepare sequences for the model (e.g., using a window size of 5 days)
WINDOW_SIZE = 5  # You can adjust this value as needed
X = []
y = []

for i in range(WINDOW_SIZE, len(scaled_data)):
    X.append(scaled_data[i-WINDOW_SIZE:i])  # Previous 5 days as input sequence
    y.append(scaled_data[i, features.index(target)])  # The target (Close price) for prediction

X = np.array(X)
y = np.array(y)

# Convert the data to PyTorch tensors
X_tensor = torch.tensor(X, dtype=torch.float32)
y_tensor = torch.tensor(y, dtype=torch.float32)

# Create a custom Dataset class for data loading
class StockDataset(Dataset):
    def __init__(self, X, y):
        self.X = X
        self.y = y

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

# Create DataLoader for prediction (without shuffle, since we are not training)
dataset = StockDataset(X_tensor, y_tensor)
data_loader = DataLoader(dataset, batch_size=1, shuffle=False)

# Load the saved model
HIDDEN_DIM = 100  # Adjust as per your model configuration
NUM_LAYERS = 2    # Adjust as per your model configuration
DROPOUT = 0.2     # Adjust as per your model configuration

model_final = LSTMModel(input_dim=X.shape[2], hidden_dim=HIDDEN_DIM, num_layers=NUM_LAYERS, dropout=DROPOUT)
model_final.load_state_dict(torch.load("lstm_model.pth"))
model_final.eval()  # Set model to evaluation mode

# Ensure the model is on the correct device (CPU or GPU)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_final.to(device)

# Make predictions on the data
predictions = []
with torch.no_grad():
    for X_batch, _ in data_loader:
        X_batch = X_batch.to(device)
        preds = model_final(X_batch).cpu().numpy()  # Get the predicted output
        predictions.append(preds)

# Convert predictions to a numpy array
predictions = np.array(predictions).ravel()

# Prepare the predictions for inverse scaling
scaled_predictions = np.hstack([predictions.reshape(-1, 1), np.zeros((len(predictions), len(features)-1))])

# Inverse scaling to get the original prices (using the scaler you used during training)
unscaled_predictions = scaler.inverse_transform(scaled_predictions)[:, 0]  # Use the first column for predictions

# Plot the predictions vs. actual data
actual_data = data[target].iloc[WINDOW_SIZE:].values  # Actual data for the same period

plt.plot(actual_data, label='Actual Prices')
plt.plot(unscaled_predictions, label='Predicted Prices', linestyle='dashed')
plt.title("Stock Price Prediction (Actual vs. Predicted)")
plt.xlabel("Days")
plt.ylabel("Price")
plt.legend()
plt.show()