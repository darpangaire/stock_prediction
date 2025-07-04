from django.shortcuts import render
import os
import numpy as np
import matplotlib as plt
import yfinance as yf
import plotly.graph_objs as go
from plotly.offline import plot
from plotly.subplots import make_subplots
import pandas as pd
from django.http import JsonResponse

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
from django.core.paginator import Paginator

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
    
from django.views.decorators.http import require_GET

@require_GET
def health_check(request):
    return JsonResponse({"status": "ok"})

  
  
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


def moving_average(series, window):
    return series.rolling(window=window).mean()

def get_multi_ticker_data(tickers, period='1mo', interval='1d'):
    return yf.download(
        tickers=tickers,
        period=period,
        interval=interval,
        group_by='ticker',
        threads=True,
        auto_adjust=True
    )

def build_stock_dashboard_figure(data, tickers):
    rows = len(tickers)
    fig = make_subplots(
        rows=rows, cols=1, shared_xaxes=True,
        specs=[[{"secondary_y": True}] for _ in range(rows)],
        vertical_spacing=0.05,
        subplot_titles=[f"{ticker}" for ticker in tickers]
    )
    for idx, ticker in enumerate(tickers):
        try:
            close = data[(ticker, 'Close')]
            volume = data[(ticker, 'Volume')]
            dates = close.index
            ma_5 = moving_average(close, 5)
            ma_20 = moving_average(close, 20)
            row = idx + 1

            # Close price
            fig.add_trace(go.Scatter(
                x=dates, y=close, mode='lines+markers',
                name=f"{ticker} Close",
                legendgroup=ticker,
                hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Close: %{y:.2f}<extra></extra>"
            ), row=row, col=1, secondary_y=False)
            # MA(5)
            fig.add_trace(go.Scatter(
                x=dates, y=ma_5, mode='lines',
                name=f"{ticker} MA(5)",
                legendgroup=ticker,
                line=dict(dash='dot'),
                hovertemplate="<b>%{x|%Y-%m-%d}</b><br>MA(5): %{y:.2f}<extra></extra>"
            ), row=row, col=1, secondary_y=False)
            # MA(20)
            fig.add_trace(go.Scatter(
                x=dates, y=ma_20, mode='lines',
                name=f"{ticker} MA(20)",
                legendgroup=ticker,
                line=dict(dash='dash'),
                hovertemplate="<b>%{x|%Y-%m-%d}</b><br>MA(20): %{y:.2f}<extra></extra>"
            ), row=row, col=1, secondary_y=False)
            # Volume
            fig.add_trace(go.Bar(
                x=dates, y=volume, name=f"{ticker} Volume",
                legendgroup=ticker,
                marker=dict(color='rgba(100,100,100,0.3)'),
                opacity=0.3,
                hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Volume: %{y}<extra></extra>",
                showlegend=False
            ), row=row, col=1, secondary_y=True)
        except Exception as e:
            print(f"Error processing {ticker}: {e}")

    fig.update_layout(
        title="Stock Dashboard: Close, MA(5/20), Volume (Last 1 Month)",
        paper_bgcolor="#14151b", plot_bgcolor="#14151b",
        font=dict(color="white"),
        height=350*len(tickers),
        legend=dict(
            orientation="h",
            x=0.5, xanchor="center", y=1.08,
            bgcolor="rgba(0,0,0,0.2)", bordercolor="white", borderwidth=1
        ),
        margin=dict(l=40, r=40, t=80, b=40)
    )
    # Y-axis labels and grid
    for i in range(1, rows+1):
        fig.update_yaxes(title_text="Price (USD)", row=i, col=1, showgrid=True, gridcolor='gray')
        fig.update_yaxes(title_text="Volume", row=i, col=1, showgrid=False, gridcolor='gray', secondary_y=True)
    fig.update_xaxes(showgrid=True, gridcolor='gray', tickformat="%Y-%m-%d")
    return fig

def get_recent_stocks_table(tickers):
    recent_data = yf.download(
        tickers=tickers,
        period='1d',
        interval='1d',
        group_by='ticker',
        auto_adjust=True,
        threads=True
    )
    recent_list = []
    for ticker in tickers:
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
    return recent_list

def home(request):
    dashboard_tickers = ['AAPL', 'AMZN', 'QCOM', 'META', 'NVDA', 'JPM']
    recent_tickers = ['AAPL', 'AMZN', 'GOOGL', 'UBER', 'TSLA']
    dashboard_data = get_multi_ticker_data(dashboard_tickers)
    fig = build_stock_dashboard_figure(dashboard_data, dashboard_tickers)
    plot_div = plot(fig, output_type='div', include_plotlyjs=False)
    recent_stocks = get_recent_stocks_table(recent_tickers)
    return render(request, 'index.html', {
        'plot_div_left': plot_div,
        'recent_stocks': recent_stocks
    })
    
def predict(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ticker = data.get('ticker')
            n_days = int(data.get('days', 1))
            predicted_prices,actual_prices, metrics, plot_history_path, plot_pred_path = run_prediction(ticker, n_days)
            # You may also want to return actual prices for the frontend
            # If you want to, add that return value to run_prediction and here
            predicted_prices = predicted_prices[0]
            prediction = Prediction.objects.create(
                user=request.user,
                ticker=ticker,
                created_at=timezone.now(),
                next_day_price=predicted_prices,
                metrics=metrics,
                plot_history_path=plot_history_path,
                plot_pred_path=plot_pred_path
            )
            return JsonResponse({
                'predicted_prices': predicted_prices,
                'actual_prices': actual_prices,  # If you want to show actual future prices, provide them here
                'metrics': metrics,
                'plot_history_path': '/' + plot_history_path if not plot_history_path.startswith('/') else plot_history_path,
                'plot_pred_path': '/' + plot_pred_path if not plot_pred_path.startswith('/') else plot_pred_path,
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return render(request, 'predict.html')


# def list_prediction(request):
#     try:
#         stocks = Prediction.objects.filter(user=request.user)
#         paginator = Paginator(stocks,4)
#         page = request.GET.get('page')
#         paged_stocks = paginator.get_page(page)
        
#         context = {
#             'stocks':paged_stocks
#         }
        
#     except:
#         stocks = None
        
#         context = {
#             'stocks':stocks
#         }
#     return render(request,'list_prediction.html',context)


