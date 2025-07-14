from django.shortcuts import render,get_object_or_404,redirect
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from api.models import TelegramUser
from django.contrib.auth import get_user_model
from .models import UserProfile
import stripe
from django.conf import settings
from .models import UserProfile
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view
from api.models import Prediction
from rest_framework.response import Response
from api.serializers import PredictionSerializers
# Create your views here.
stripe.api_key = settings.STRIPE_SECRET_KEY

def success(request):
    user = request.user
    telegram,created = TelegramUser.objects.get_or_create(user=user)
    userprofile,created = UserProfile.objects.get_or_create(user=telegram)
    userprofile.is_pro = True
    userprofile.save()
    
    return render(request,'success.html')

def cancel(request):
  return render(request,'unsuccess.html')

User = get_user_model()  

@method_decorator(csrf_exempt, name='dispatch')
class CreatePaymentView(LoginRequiredMixin, View):
    def post(self, request, user_id):
        webuser = get_object_or_404(User, id=user_id)
        telegram_user, created = TelegramUser.objects.get_or_create(user=webuser)
        userprofile, created = UserProfile.objects.get_or_create(user=telegram_user)
        try:
            checkout_session = stripe.checkout.Session.create(
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': 'Pro Subscription',
                            },
                            'unit_amount': 6000,
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url='http://localhost:8000/success/',
                cancel_url='http://localhost:8000/cancel/',
                client_reference_id=str(request.user.id),
            )
            userprofile.stripe_subscription_id = checkout_session.id
            userprofile.save()
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

        return redirect(checkout_session.url, code=303)




from django.http import HttpResponse



@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    endpoint_secret = 'your_webhook_signing_secret'  # from your Stripe dashboard

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return JsonResponse({'status': 'invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return JsonResponse({'status': 'invalid signature'}, status=400)

    # Handle successful checkout session
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        client_reference_id = session.get('client_reference_id')
        stripe_session_id = session.get('id')

        # Find the user by client_reference_id
        user = User.objects.get(id=client_reference_id)
        telegram_user, _ = TelegramUser.objects.get_or_create(user=user)
        userprofile, _ = UserProfile.objects.get_or_create(user=telegram_user)

        userprofile.is_pro = True
        userprofile.stripe_subscription_id = stripe_session_id
        userprofile.save()

    return JsonResponse({'status': 'success'}, status=200)



@login_required(login_url='login')
def profile(request):
    chance = 0
    telegram_user,created = TelegramUser.objects.get_or_create(user=request.user)
    userprofile,created = UserProfile.objects.get_or_create(user=telegram_user)
    
    chance = 5 - int(userprofile.daily_prediction_count)
    if chance <=0:
        chance = 0 
    
    context = {
        'userprofile':userprofile,
        'chance':chance,
        
    }

    return render(request,'payment.html',context)



@api_view(['GET'])
def list_prediction(request):
    predictions = Prediction.objects.filter(user = request.user)
    serializers = PredictionSerializers(predictions,many=True)
    
    return JsonResponse({"predictions":serializers.data})

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

class List_prediction(generics.ListAPIView):
    serializer_class = PredictionSerializers
    
    def get_queryset(self):
        return Prediction.objects.filter(user=self.request.user)


