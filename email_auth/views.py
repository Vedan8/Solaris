from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers, status
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
import random
from .models import Subscriber
from .serializers import SubscriberSerializer

# Temporary in-memory storage for OTPs and user data
otp_storage = {}

User = get_user_model()  # Use the custom user model


def generate_otp():
    """Generate a 6-digit random OTP."""
    return random.randint(100000, 999999)


class SignupApi(APIView):
    """API for user signup with email and password."""
    
    class InputSerializer(serializers.Serializer):
        email = serializers.EmailField()
        password = serializers.CharField(write_only=True, min_length=8)

    def post(self, request, *args, **kwargs):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "A user with this email already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        otp = generate_otp()
        otp_storage[email] = {
            "password": make_password(password),  # Hash the password
            "otp": otp,
        }

        # Send the OTP via email
        send_mail(
            subject="Your OTP Code",
            message=f"Your OTP code is {otp}.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )

        return Response({"message": "OTP sent to your email."}, status=status.HTTP_200_OK)


class VerifyOtpApi(APIView):
    """API to verify OTP and complete registration."""
    
    class InputSerializer(serializers.Serializer):
        email = serializers.EmailField()
        otp = serializers.IntegerField()

    def post(self, request, *args, **kwargs):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']

        if email not in otp_storage or otp_storage[email]['otp'] != otp:
            return Response(
                {"error": "Invalid OTP or email."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create the user
        User.objects.create_user(
            username=email.split("@")[0],  # Use the part before @ as username
            email=email,
            password=otp_storage[email]['password'],  # Already hashed
        )
        del otp_storage[email]

        return Response({"message": "User registered successfully."}, status=status.HTTP_201_CREATED)


class LoginApi(APIView):
    """API for user login using email and password."""
    
    class InputSerializer(serializers.Serializer):
        email = serializers.EmailField()
        password = serializers.CharField(write_only=True)

    def post(self, request, *args, **kwargs):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid email"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Debug: Print the entered password and the stored hashed password

        # Use check_password to verify the hashed password
        if not user.check_password(password):
            return Response(
                {"error": "Invalid password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_200_OK,
        )

class SubscriberView(APIView):
    def post(self,request):
        serializer=SubscriberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        Subscriber.objects.create(email=email)
        return Response(
            {
                "User Suscribed"
            },
            status=status.HTTP_200_OK,
        )



