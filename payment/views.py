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
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session["client_reference_id"]
        user = User.objects.get(id=user_id)
        user.userprofile.is_pro = True
        user.userprofile.save()

    return HttpResponse(status=200)


@login_required(login_url='login')
def profile(request):
    telegram_user,created = TelegramUser.objects.get_or_create(user=request.user)
    userprofile,created = UserProfile.objects.get_or_create(user=telegram_user)
    chance = 5 - int(userprofile.daily_prediction_count)
    context = {
        'userprofile':userprofile,
        'chance':chance,
        
    }

    return render(request,'payment.html',context)




