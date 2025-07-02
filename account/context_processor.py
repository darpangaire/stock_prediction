from django.conf import settings
from django.contrib.auth import get_user_model
import jwt
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.utils import timezone

User = get_user_model()

def get_user_from_jwt(request):
    access_token = request.COOKIES.get('jwt')
    refresh_token = request.COOKIES.get('refresh')
    user = None

    if access_token:
        try:
            payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=['HS256'])
            user = User.objects.get(id=payload['user_id'])
        except jwt.ExpiredSignatureError:
            # Try refreshing using refresh token
            if refresh_token:
                try:
                    refresh = RefreshToken(refresh_token)
                    new_access = str(refresh.access_token)

                    # Update cookie
                    request._jwt_new_access_token = new_access  # Store it so middleware or response can set cookie

                    payload = jwt.decode(new_access, settings.SECRET_KEY, algorithms=['HS256'])
                    user = User.objects.get(id=payload['user_id'])

                except Exception as e:
                    # Refresh token is also invalid or expired
                    user = None
            else:
                user = None
        except (jwt.DecodeError, User.DoesNotExist):
            user = None

    return {"user": user}
