from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    SignupView, VerifyOTPView, ResendOTPView,
    ForgotPasswordView, ResetPasswordView, LoginView , UpdateUserTypeView
)

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend_otp'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('login/', LoginView.as_view(), name='login'),  # Login endpoint
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Refresh token endpoint
    path('usertype/', UpdateUserTypeView.as_view(), name='update_usertype'),
]
