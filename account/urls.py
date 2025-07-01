from django.urls import path
from .views import UserRegistrationView,UserLoginView,register_view,email_verification_alert,login_view,verify_email_and_redirect,logout_view

urlpatterns = [
  path("api-register/",UserRegistrationView.as_view(),name='apiRegister'),
  
  path('api-login/',UserLoginView.as_view(),name='api-login'),
  
  path('register/',register_view,name='register'),
  path('email-verification-alert/', email_verification_alert, name='email_verification_alert'),
  path("verify-email/<uidb64>/<token>/", verify_email_and_redirect, name='verify-email-redirect'),
  
  path('login/',login_view,name='login'),
  path('logout/',logout_view,name='logout'),

  
]





