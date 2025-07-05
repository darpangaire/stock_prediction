from django.urls import path
from .views import success,cancel,CreatePaymentView,stripe_webhook,profile

urlpatterns = [
  path('success/',success,name="success"),
  path('cancel/',cancel,name="cancel"),
  path('paymentview/<int:user_id>',CreatePaymentView.as_view(),name="paymentview"),
  path('pay/',profile,name="pay"),
  path("webhooks/stripe/", stripe_webhook, name="stripe_webhook"),
  path('profile/',profile,name='profile')
  
]

