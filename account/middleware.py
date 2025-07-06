# account/middleware.py

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class JWTAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        access_token = request.COOKIES.get('jwt')
        refresh_token = request.COOKIES.get('refresh')

        if access_token:
            try:
                payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=['HS256'])
                user = User.objects.get(id=payload['user_id'])
                request.user = user
            except jwt.ExpiredSignatureError:
                # Try to refresh
                if refresh_token:
                    try:
                        refresh = RefreshToken(refresh_token)
                        new_access = str(refresh.access_token)

                        # Save new token to set in response later
                        request._jwt_new_access_token = new_access

                        payload = jwt.decode(new_access, settings.SECRET_KEY, algorithms=['HS256'])
                        user = User.objects.get(id=payload['user_id'])
                        request.user = user
                    except Exception:
                        request.user = AnonymousUser()
                else:
                    request.user = AnonymousUser()
            except (jwt.DecodeError, User.DoesNotExist):
                request.user = AnonymousUser()
        else:
            request.user = AnonymousUser()

        response = self.get_response(request)

        # Set new access token if refreshed
        if hasattr(request, '_jwt_new_access_token'):
            response.set_cookie(
                key="jwt",
                value=request._jwt_new_access_token,
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
                max_age=3600
            )
        return response
