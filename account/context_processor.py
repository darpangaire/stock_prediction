from django.conf import settings
from django.contrib.auth import get_user_model
import jwt


def get_user_from_jwt(request):
  token = request.COOKIES.get('jwt')
  user = None

  if token:
      try:
          payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
          user = get_user_model().objects.get(id=payload['user_id'])
      except (jwt.ExpiredSignatureError, jwt.DecodeError, get_user_model().DoesNotExist):
          user = None

  return {"user": user}  # ✅ Always return a dictionary




