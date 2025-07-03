class RefreshAccessTokenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if hasattr(request, '_jwt_new_access_token'):
            response.set_cookie(
                'jwt',
                request._jwt_new_access_token,
                httponly=True,
                samesite='Lax',
                path='/',
                secure=False,  # True in production with HTTPS
            )
        return response