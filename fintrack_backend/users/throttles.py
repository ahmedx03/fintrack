from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """5 login attempts per minute per IP."""
    scope = 'auth_login'


class RegisterRateThrottle(AnonRateThrottle):
    """10 registrations per hour per IP."""
    scope = 'auth_register'
