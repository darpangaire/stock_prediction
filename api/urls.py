from django.urls import path
from .views import predict_api,home,predict,health_check,list_prediction_data

urlpatterns = [
  path('api/predict/', predict_api),
  # path('api/predictions/', list_predictions),
  path('healthz/', health_check),
  
  path('', home,name='home'),
  path('prediction/', predict,name='predict'),
  # path('list_prediction/', list_prediction_data,name='list_prediction_data'),

]


