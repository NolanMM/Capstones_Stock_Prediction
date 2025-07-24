from rest_framework.authentication import SessionAuthentication

class CsrfExemptSessionAuthentication(SessionAuthentication):
    """Session authentication without CSRF enforcement for SPA usage."""
    def enforce_csrf(self, request):
        return
