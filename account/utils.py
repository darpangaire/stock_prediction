from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse



def send_verification_email(user,request):
  token = default_token_generator.make_token(user)
  uid = urlsafe_base64_encode(force_bytes(user.id))
  domain = request.get_host()
  verification_link = f"http://{domain}/account/verify-email/{ uid }/{ token }/"
  subject = "verify your email"
  message = f"hi {user.first_name},\n\nPlease verify your email by clicking the link below:\n{verification_link}\n\nThanks!"
  
  send_mail(
    subject,
    message,
    settings.EMAIL_HOST_USER,
    [user.email],
    fail_silently=False
    
  )
  # path('channels/<int:id>/', channel_details, name='channel_details'),
  
def sending_email(request,post):
  domain = request.get_host()
  link = f"http://{domain}/channels/{post.channel.id}/"
  message = f''' This channel {post.channel.name} has some comments so please watch this.
  {link}
  '''
  subject = "alert about your channels"
  
  send_mail(
    subject,
    message,
    settings.EMAIL_HOST_USER,
    [post.channel.admin],
    fail_silently=False,
    
  )
  
    