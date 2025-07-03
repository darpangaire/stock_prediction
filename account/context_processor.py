from django.conf import settings
from django.contrib.auth import get_user_model
import jwt
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import authentication, exceptions

User = get_user_model()

class JWTFromCookieAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):        
        access_token = request.COOKIES.get('jwt')
        refresh_token = request.COOKIES.get('refresh')
        user = None

        if access_token:
            try:
                payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=['HS256'])
                user = User.objects.get(id=payload['user_id'])
                return (user, access_token)
            except jwt.ExpiredSignatureError:
                # Try refreshing using refresh token
                if refresh_token:
                    try:
                        refresh = RefreshToken(refresh_token)
                        new_access = str(refresh.access_token)

                        # Store new access to set in response later (middleware/response handler needed)
                        request._jwt_new_access_token = new_access

                        payload = jwt.decode(new_access, settings.SECRET_KEY, algorithms=['HS256'])
                        user = User.objects.get(id=payload['user_id'])
                        return (user, new_access)
                    except Exception:
                        raise exceptions.AuthenticationFailed('Refresh token is invalid or expired')
                else:
                    raise exceptions.AuthenticationFailed('Access token expired and no refresh token')
            except (jwt.DecodeError, User.DoesNotExist):
                raise exceptions.AuthenticationFailed('Invalid token or user not found')
        return None