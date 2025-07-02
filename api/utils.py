import os

import numpy as np
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, r2_score
from tensorflow.keras.models import load_model
from django.conf import settings
import matplotlib.pyplot as plt

def run_prediction(ticker):
    df = yf.download(ticker, period='10y', interval='1d')
    
    if df.empty:
        raise ValueError("No data found for ticker")
    
    close_prices = df['Close'].values.reshape(-1, 1)
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_close = scaler.fit_transform(close_prices)

    # For the next-day price prediction
    last_60 = scaled_close[-60:]
    X_input = np.expand_dims(last_60, axis=0)

    model_path = getattr(settings, "MODEL_PATH", "stock_prediction_model1.keras")
    if not os.path.exists(model_path):
        raise FileNotFoundError("Model file not found")
    
    model = load_model(model_path)
    
    # Predict next-day price
    predicted_scaled = model.predict(X_input, verbose=0)
    predicted_price = scaler.inverse_transform(predicted_scaled)[0][0]

    # Prepare data for evaluating metrics
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

    # Pred vs True plot
    plt.figure(figsize=(10, 4))
    plt.plot(test_true.flatten(), label="True Price")
    plt.plot(test_preds.flatten(), label="Predicted Price")
    plt.title(f"{ticker} Predicted vs True (Last {n_test_points} days)")
    plt.legend()
    plt.savefig(plot_pred_path)
    plt.close()

    metrics = {"mse": mse, "rmse": rmse, "r2": r2}
    return predicted_price, metrics, plot_history_path, plot_pred_path



