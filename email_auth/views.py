from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from random import randint
from django.utils.timezone import now
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed

from .models import CustomUser, TemporaryUser
from .serializers import (
    SignupSerializer, VerifyOTPSerializer,
    ResendOTPSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
)

class SignupView(APIView):
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'OTP sent to email'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyOTPView(APIView):
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            try:
                temp_user = TemporaryUser.objects.get(email=serializer.validated_data['email'])
                if temp_user.otp != serializer.validated_data['otp']:
                    return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
                if temp_user.is_otp_expired():
                    return Response({'error': 'OTP expired. Please request a new OTP.'}, status=status.HTTP_400_BAD_REQUEST)

                # Create the permanent user
                user = CustomUser.objects.create_user(
                    email=temp_user.email,
                    password=temp_user.password
                )
                temp_user.delete()  # Remove temporary user after success
                return Response({'message': 'User verified and created successfully'}, status=status.HTTP_201_CREATED)
            except TemporaryUser.DoesNotExist:
                return Response({'error': 'Email not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResendOTPView(APIView):
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if serializer.is_valid():
            try:
                temp_user = TemporaryUser.objects.get(email=serializer.validated_data['email'])
                temp_user.otp = str(randint(100000, 999999))
                temp_user.otp_created_at = now()
                temp_user.save()
                send_mail(
                    "Your New OTP Code",
                    f"Your new OTP code is {temp_user.otp}",
                    'from@example.com',
                    [temp_user.email],
                )
                return Response({'message': 'New OTP sent to email'}, status=status.HTTP_200_OK)
            except TemporaryUser.DoesNotExist:
                return Response({'error': 'Email not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ForgotPasswordView(APIView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = CustomUser.objects.get(email=serializer.validated_data['email'])
                otp = str(randint(100000, 999999))
                TemporaryUser.objects.update_or_create(
                    email=user.email,
                    defaults={
                        'password': user.password,
                        'otp': otp,
                        'otp_created_at': now(),
                    },
                )
                send_mail(
                    "Your Password Reset OTP",
                    f"Your OTP code is {otp}",
                    'from@example.com',
                    [user.email],
                )
                return Response({'message': 'OTP sent to email'}, status=status.HTTP_200_OK)
            except CustomUser.DoesNotExist:
                return Response({'error': 'Email not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            try:
                temp_user = TemporaryUser.objects.get(email=serializer.validated_data['email'])
                if temp_user.otp != serializer.validated_data['otp']:
                    return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
                if temp_user.is_otp_expired():
                    return Response({'error': 'OTP expired. Please request a new OTP.'}, status=status.HTTP_400_BAD_REQUEST)

                user = CustomUser.objects.get(email=temp_user.email)
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                temp_user.delete()  # Remove the temporary record after reset
                return Response({'message': 'Password reset successfully'}, status=status.HTTP_200_OK)
            except (TemporaryUser.DoesNotExist, CustomUser.DoesNotExist):
                return Response({'error': 'Invalid email or OTP'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        if not user.is_active:
            raise AuthenticationFailed('Account is not verified. Please verify your email.')

        return data

class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer