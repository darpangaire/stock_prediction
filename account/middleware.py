# from django.contrib.auth import get_user_model
# from django.contrib.auth.models import AnonymousUser
# from django.utils.deprecation import MiddlewareMixin
# from rest_framework_simplejwt.authentication import JWTAuthentication
# from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
# import logging

# logger = logging.getLogger(__name__)

# User = get_user_model()

# class JWTAuthMiddleware(MiddlewareMixin):
#     def process_request(self, request):
#         token = request.COOKIES.get('access_token')
#         logger.debug(f"Token found: {token}")
#         if token:
#             try:
#                 # Use Simple JWT's authentication to validate token
#                 validated_token = JWTAuthentication().get_validated_token(token)
#                 user = JWTAuthentication().get_user(validated_token)
#                 logger.debug(f"Authenticated user: {user}")
#                 request.user = user
#             except (InvalidToken, TokenError) as e:
#                 logger.error(f"Token error: {str(e)}")
#                 request.user = AnonymousUser()
#             except User.DoesNotExist:
#                 logger.error("User does not exist")
#                 request.user = AnonymousUser()
#         else:
#             logger.debug("No token found")
#             request.user = AnonymousUser()