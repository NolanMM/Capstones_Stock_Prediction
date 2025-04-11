# convert_model_to_pickle.py

import torch
import pickle
import torch.nn as nn

# Define your LSTMModel architecture 
class LSTMModel(nn.Module):
    def __init__(self, input_dim, hidden_dim=100, num_layers=2, dropout=0.2):
        super(LSTMModel, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, dropout=dropout, batch_first=True)
        self.fc = nn.Linear(hidden_dim, 1)

    def forward(self, x):
        batch_size = x.size(0)
        # Initialize hidden state and cell state with zeros
        h0 = torch.zeros(self.num_layers, batch_size, self.hidden_dim, device=x.device)
        c0 = torch.zeros(self.num_layers, batch_size, self.hidden_dim, device=x.device)
        out, _ = self.lstm(x, (h0, c0))
        out = out[:, -1, :]  # use the output from the last time step
        out = self.fc(out)
        return out

# Specify model file path
model_path = r"lstm_model.model"

state_dict = torch.load(model_path, map_location=torch.device("cpu"))

input_dim = 9  # Change this value as needed
model = LSTMModel(input_dim=input_dim, hidden_dim=100, num_layers=2, dropout=0.2)

# Load the state dictionary into the model
model.load_state_dict(state_dict)

# Set the model to evaluation mode
model.eval()

# Now, save the fully instantiated model with pickle
pickle_path = "lstm_model.pkl"
with open(pickle_path, "wb") as f:
    pickle.dump(model, f)

print(f"Model successfully saved as a pickle file at {pickle_path}")
