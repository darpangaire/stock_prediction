from django.urls import path
from .views import predict_api, list_predictions,home,predict

urlpatterns = [
  path('predict/', predict_api),
  path('predictions/', list_predictions),
  
  path('', home,name='home'),
  path('prediction/', predict,name='prediction'),

]

