from django.urls import path
from .views import predict_api, list_predictions,home,predict,health_check

urlpatterns = [
  path('api/predict/', predict_api),
  path('api/predictions/', list_predictions),
  path('healthz/', health_check),
  
  path('', home,name='home'),
  path('prediction/', predict,name='predict'),
  # path('list_prediction/', list_prediction,name='list_prediction'),

]


