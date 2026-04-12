
class ActivityLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Log login/logout actions
        if request.path in ("/accounts/login/", "/accounts/logout/") and request.method == "POST":
            try:
                from .models import ActivityLog
                action = "Logged in" if "login" in request.path else "Logged out"
                user = request.user if request.user.is_authenticated else None
                ip = request.META.get("HTTP_X_FORWARDED_FOR","").split(",")[0].strip() or request.META.get("REMOTE_ADDR","")
                ActivityLog.objects.create(user=user, action=action, ip_address=ip or None,
                    user_agent=request.META.get("HTTP_USER_AGENT","")[:200])
            except Exception:
                pass
        return response
