from django.shortcuts import render
import os
import numpy as np
import matplotlib as plt
import yfinance as yf

from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from django.utils import timezone

from .models import Prediction
from .serializers import PredictionSerializers
from .utils import run_prediction
from account.backends import get_user_from_jwt_for_backend

# Create your views here.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict_api(request):
  ticker = request.data.get('ticker')
  if not ticker:
    return Response({"error":"Ticker is required"},status=400)
  
  user = get_user_from_jwt_for_backend(request)
  
  try:
    price,metrics,hist_path,pred_path = run_prediction(ticker)
    prediction = Prediction.objects.create(
      user = user,
      ticker = ticker,
      created_at = timezone.now(),
      next_day_price = price,
      metrics = metrics,
      plot_history_path=hist_path,
      plot_pred_path = pred_path
      
    )
    serializer = PredictionSerializers(prediction)
    return Response(serializer.data)
  
  except Exception as e:
    import traceback
    traceback.print_exc()  # This will show full error in console
    return Response({"error": str(e)}, status=500)
  
  
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_predictions(request):
  ticker_filter = request.query_params.get("ticker")
  date_filter = request.query_params.get("date")
  
  user = get_user_from_jwt_for_backend(request)
  qs = Prediction.objects.filter(user=user)
  
  if ticker_filter:
    qs = qs.filter(ticker__iexact = ticker_filter)
    
  if date_filter:
    qs = qs.filter(created_at__date=date_filter)
  
  serializer = PredictionSerializers(qs.order_by("-created_at"),many=True)
  return Response(serializer.data)



def home(request):
  return render(request,'index.html')


