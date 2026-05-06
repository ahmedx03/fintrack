from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import RegisterView, MeView, LogoutView
from .throttles import LoginRateThrottle


# Apply the login throttle directly on the JWT view
class ThrottledTokenObtainPairView(TokenObtainPairView):
    throttle_classes = (LoginRateThrottle,)


urlpatterns = [
    path('register/', RegisterView.as_view(),              name='auth-register'),
    path('login/',    ThrottledTokenObtainPairView.as_view(), name='auth-login'),
    path('refresh/',  TokenRefreshView.as_view(),          name='auth-refresh'),
    path('me/',       MeView.as_view(),                    name='auth-me'),
    path('logout/',   LogoutView.as_view(),                name='auth-logout'),
]
