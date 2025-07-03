from django.shortcuts import render
import os
import numpy as np
import matplotlib as plt
import yfinance as yf
import plotly.graph_objs as go
from plotly.offline import plot
import pandas as pd

from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from django.utils import timezone
import json

from .models import Prediction
from .serializers import PredictionSerializers
from .utils import run_prediction
from django.contrib.auth.decorators import login_required

# Create your views here.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict_api(request):
    ticker = request.data.get('ticker')
    n_days = int(request.data.get('number_of_days', 1))  # Default to 1 if not provided

    if not ticker:
        return Response({"error": "Ticker is required"}, status=400)

    user = request.user

    try:
        price, metrics, hist_path, pred_path = run_prediction(ticker, n_days) # Pass n_days here!
        if isinstance(price,list):
            price = price[0]  
        prediction = Prediction.objects.create(
            user=user,
            ticker=ticker,
            created_at=timezone.now(),
            next_day_price=price,
            metrics=metrics,
            plot_history_path=hist_path,
            plot_pred_path=pred_path
        )
        serializer = PredictionSerializers(prediction)
        return Response(serializer.data)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=500)
  
  
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_predictions(request):
  ticker_filter = request.query_params.get("ticker")
  date_filter = request.query_params.get("date")
  
  user = request.user
  qs = Prediction.objects.filter(user=user)
  
  if ticker_filter:
    qs = qs.filter(ticker__iexact = ticker_filter)
    
  if date_filter:
    qs = qs.filter(created_at__date=date_filter)
  
  serializer = PredictionSerializers(qs.order_by("-created_at"),many=True)
  return Response(serializer.data)



def home(request):
    # --- SETUP ---
    tickers_plot = ['AAPL', 'AMZN', 'QCOM', 'META', 'NVDA', 'JPM']
    period = '1mo'
    interval = '1d'

    # --- DATA FETCHING ---
    # Download all data in one call for efficiency
    data = yf.download(
        tickers=tickers_plot,
        period=period,
        interval=interval,
        group_by='ticker',
        threads=True,
        auto_adjust=True  # Use adjusted close for all columns
    )

    # --- DATA PROCESSING & PLOTTING ---
    fig = go.Figure()
    for ticker in tickers_plot:
        try:
            # Extract close and volume series
            close = data[(ticker, 'Close')]
            volume = data[(ticker, 'Volume')]
            dates = close.index

            # Calculate moving averages for more detail
            ma_5 = close.rolling(window=5).mean()
            ma_20 = close.rolling(window=20).mean()

            # Plot close price
            fig.add_trace(go.Scatter(
                x=dates,
                y=close,
                mode='lines+markers',
                name=f"{ticker} Close",
                hovertemplate=f"<b>{ticker}</b><br>Date: %{{x|%Y-%m-%d}}<br>Close: %{{y:.2f}}<extra></extra>"
            ))
            # Plot short-term moving average
            fig.add_trace(go.Scatter(
                x=dates,
                y=ma_5,
                mode='lines',
                name=f"{ticker} MA(5)",
                line=dict(dash='dot'),
                hovertemplate=f"<b>{ticker} MA(5)</b><br>Date: %{{x|%Y-%m-%d}}<br>MA(5): %{{y:.2f}}<extra></extra>"
            ))
            # Plot long-term moving average
            fig.add_trace(go.Scatter(
                x=dates,
                y=ma_20,
                mode='lines',
                name=f"{ticker} MA(20)",
                line=dict(dash='dash'),
                hovertemplate=f"<b>{ticker} MA(20)</b><br>Date: %{{x|%Y-%m-%d}}<br>MA(20): %{{y:.2f}}<extra></extra>"
            ))

            # Optionally, add volume as a secondary y-axis (shared x)
            fig.add_trace(go.Bar(
                x=dates,
                y=volume,
                name=f"{ticker} Volume",
                yaxis='y2',
                opacity=0.2,
                marker=dict(color='rgba(100,100,100,0.3)'),
                hovertemplate=f"<b>{ticker}</b><br>Date: %{{x|%Y-%m-%d}}<br>Volume: %{{y}}<extra></extra>"
            ))
        except KeyError:
            print(f"No data for {ticker}")

    # --- LAYOUT ENHANCEMENTS ---
    fig.update_layout(
        title="Modern Stock Market Dashboard: Close Price, MAs, and Volume (Last 1 Month)",
        paper_bgcolor="#14151b",
        plot_bgcolor="#14151b",
        font=dict(color="white"),
        xaxis=dict(
            title="Date",
            showgrid=True, 
            gridcolor='gray',
            rangeselector=dict(
                buttons=list([
                    dict(count=7, label="1w", step="day", stepmode="backward"),
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(visible=True),
            type="date"
        ),
        yaxis=dict(
            title="Price (USD)",
            showgrid=True,
            gridcolor='gray'
        ),
        yaxis2=dict(
            title="Volume",
            overlaying='y',
            side='right',
            showgrid=False,
            gridcolor='gray'
        ),
        legend=dict(
            title="Legend",
            orientation="h",
            x=0.5,
            xanchor="center",
            y=1.1,
            yanchor="top",
            bgcolor="rgba(0,0,0,0.2)",
            bordercolor="white",
            borderwidth=1
        ),
        margin=dict(l=40, r=40, t=80, b=40),
        hovermode='x unified',
        bargap=0.15,
        bargroupgap=0.1,
        height=600
    )

    plot_div = plot(fig, output_type='div', include_plotlyjs=False)

    # --- RECENT STOCKS TABLE ---
    tickers_recent = ['AAPL', 'AMZN', 'GOOGL', 'UBER', 'TSLA']
    recent_list = []
    recent_data = yf.download(
        tickers=tickers_recent,
        period='1d',
        interval='1d',
        group_by='ticker',
        auto_adjust=True,
        threads=True
    )

    for ticker in tickers_recent:
        try:
            row = recent_data.loc[:, ticker].iloc[0]
            recent_list.append({
                "Ticker": ticker,
                "Open": float(row["Open"]),
                "High": float(row["High"]),
                "Low": float(row["Low"]),
                "Close": float(row["Close"]),
                "Volume": int(row["Volume"]),
            })
        except Exception as e:
            print(f"No data for {ticker}: {e}")

    # --- RENDERING ---
    return render(request, 'index.html', {
        'plot_div_left': plot_div,
        'recent_stocks': recent_list
    })
    
def predict(request):  
    # if request.method == 'POST':
    #     ticker = request.data.get('ticker')
    #     n_days = int(request.data.get('number_of_days', 1))
    #     try:
    #         price, metrics, hist_path, pred_path = run_prediction(ticker, n_days)
            
    #     except:
    #         pass
        
    #     context = {
    #         'predicted_price':price,
    #         'hist_path':hist_path,
    #         'pred_path':pred_path,
    #     }
        
             
    return render(request,'predict.html')



