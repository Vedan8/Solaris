from django.urls import path
from .views import SignupApi, VerifyOtpApi, LoginApi, SubscriberView

urlpatterns = [
    path('signup/', SignupApi.as_view(), name='email-signup'),
    path('verify-otp/', VerifyOtpApi.as_view(), name='verify-otp'),
    path('login/', LoginApi.as_view(), name='email-login'),
    path('suscriber/', SubscriberView.as_view(), name='suscriber')
]
