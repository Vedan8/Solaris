from django.urls import path
from .views import GoogleLoginRedirectApi, GoogleLoginApi

urlpatterns = [
    path('google/login/', GoogleLoginRedirectApi.as_view(), name='google-login-redirect'),
    path('google/callback/', GoogleLoginApi.as_view(), name='google-login-callback'),
    path('google-oauth2/login/raw/callback/', GoogleLoginApi.as_view(), name='google-login-raw-callback'),
]
