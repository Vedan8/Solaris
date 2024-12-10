from rest_framework import serializers
from .models import CustomUser, TemporaryUser
from django.core.mail import send_mail
from random import randint
from django.utils.timezone import now

class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def create(self, validated_data):
        otp = str(randint(100000, 999999))
        temporary_user, created = TemporaryUser.objects.update_or_create(
            email=validated_data['email'],
            defaults={
                'password': validated_data['password'],  # Store plain hashed password
                'otp': otp,
                'otp_created_at': now(),
            },
        )
        send_mail(
            "Your OTP Code",
            f"Your OTP code is {otp}. Valid for 5 minutes",
            'Solaris@gmail.com',
            [validated_data['email']],
        )
        return temporary_user

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)
