from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers, status
from django.core.mail import send_mail
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password, check_password
from .models import Subscriber
from .serializers import SubscriberSerializer
import random
from .jwt_compat import InvalidKeyError, InvalidAlgorithmError, InvalidTokenError

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
            "password": password,
            "otp": otp,
        }

        # Send the OTP via email
        try:
            send_mail(
                subject="Your OTP Code",
                message=f"Your OTP code is {otp}.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to send OTP: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
        try:
            user = User(
                username=email.split("@")[0],
                email=email,
            )
            user.set_password(otp_storage[email]['password'])
            user.save()
            del otp_storage[email]
        except Exception as e:
            return Response(
                {"error": f"User registration failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

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

        User = get_user_model()

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid email"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Validate password
        if not user.check_password(password):
            return Response({"error": "Invalid password."}, status=status.HTTP_401_UNAUTHORIZED)

        # Generate JWT tokens with comprehensive error handling
        try:
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                status=status.HTTP_200_OK,
            )
        except (InvalidKeyError, InvalidAlgorithmError, InvalidTokenError) as e:
            return Response(
                {"error": f"Token generation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            return Response(
                {"error": f"Unexpected error during token generation: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SubscriberView(APIView):
    """API to subscribe a user. Only accessible to authenticated users."""
    
    class InputSerializer(serializers.Serializer):
        email = serializers.EmailField()

    def post(self, request):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return Response(
                {"error": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        
        try:
            Subscriber.objects.create(email=email)
        except Exception as e:
            return Response(
                {"error": f"Subscription failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
        return Response(
            {"message": "User subscribed successfully."},
            status=status.HTTP_200_OK,
        )