import os

import numpy as np
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, r2_score
from tensorflow.keras.models import load_model
from django.conf import settings
import matplotlib.pyplot as plt

def run_prediction(ticker, n_days=1):
    """
    Predict the next n_days closing prices for a given stock ticker using a trained LSTM model.
    Returns:
        predicted_prices: list of float
        metrics: dict of mse, rmse, r2 (for test set, not the n_days predicted)
        plot_history_path: str, path to saved historical price plot
        plot_pred_path: str, path to saved prediction vs true plot
    """
    # Download historical data
    df = yf.download(ticker, period='10y', interval='1d')
    if df.empty:
        raise ValueError("No data found for ticker")

    close_prices = df['Close'].values.reshape(-1, 1) # reshape is for making 2d data and (3, 1) 3 mean -1  = ? rows and 1 = want 1 column
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_close = scaler.fit_transform(close_prices)

    # Prepare input for multi-day prediction
    last_60 = scaled_close[-60:]      # shape (60, 1)
    X_input = last_60.flatten()       # shape (60,)

    # Load model
    model_path = getattr(settings, "MODEL_PATH", "stock_prediction_model1.keras")
    if not os.path.exists(model_path):
        raise FileNotFoundError("Model file not found")

    model = load_model(model_path)

    # Predict next n_days using rolling window
    predicted_prices = []
    current_input = X_input.copy() # X_input is a 1D array of shape (60,)
    for _ in range(n_days): # Each loop iteration = predict 1 day ahead.
        input_reshaped = np.expand_dims(current_input, axis=(0, 2))  #np.expand_dims(current_input, axis=(0, 2)): shape (1, 60, 1)
        pred_scaled = model.predict(input_reshaped, verbose=0)
        pred_price = scaler.inverse_transform(pred_scaled)[0][0]
        predicted_prices.append(float(pred_price))
        # Update input for next prediction
        current_input = np.append(current_input, pred_scaled)[-60:]

    # Prepare data for evaluating metrics (on last 100 test points)
    n_steps = 60
    n_test_points = 100
    if len(scaled_close) < n_steps + n_test_points:
        raise ValueError("Not enough data for testing metrics")

    test_preds_scaled = []
    for i in range(n_test_points):
        start_idx = -(n_test_points + n_steps - i)
        end_idx = -(n_test_points - i)
        X_test_seq = scaled_close[start_idx:end_idx]
        X_test_seq = np.expand_dims(X_test_seq, axis=0)
        pred_scaled = model.predict(X_test_seq, verbose=0)
        test_preds_scaled.append(pred_scaled[0][0])

    test_preds_scaled = np.array(test_preds_scaled).reshape(-1, 1)
    test_preds = scaler.inverse_transform(test_preds_scaled)
    test_true = close_prices[-n_test_points:]

    mse = float(mean_squared_error(test_true.flatten(), test_preds.flatten()))
    rmse = float(np.sqrt(mse))
    r2 = float(r2_score(test_true.flatten(), test_preds.flatten()))

    # Make plots
    os.makedirs("static/plots", exist_ok=True)
    plot_history_path = f"static/plots/{ticker}_history.png"
    plot_pred_path = f"static/plots/{ticker}_pred.png"

    # History plot (raw closing prices)
    plt.figure(figsize=(10, 4))
    plt.plot(close_prices, label="Close Price")
    plt.title(f"{ticker} Price History")
    plt.legend()
    plt.savefig(plot_history_path)
    plt.close()

    # Pred vs True plot (last n_test_points)
    plt.figure(figsize=(10, 4))
    plt.plot(test_true.flatten(), label="True Price")
    plt.plot(test_preds.flatten(), label="Predicted Price")
    plt.title(f"{ticker} Predicted vs True (Last {n_test_points} days)")
    plt.legend()
    plt.savefig(plot_pred_path)
    plt.close()

    metrics = {"mse": mse, "rmse": rmse, "r2": r2}
    actual_prices = [float(p) for p in close_prices[-n_days:]]

    return predicted_prices,actual_prices, metrics, plot_history_path, plot_pred_path