class UserAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Import inside method to avoid circular imports
        try:
            from register_login.views import current_user
            # Set current_user as request attribute
            request.current_user = current_user
        except ImportError:
            request.current_user = {}
        
        response = self.get_response(request)
        return response