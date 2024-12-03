from rest_framework.views import APIView
from django.shortcuts import redirect
from django.contrib.auth import login
from rest_framework.response import Response
from rest_framework import serializers, status
from .google_login_service import GoogleRawLoginFlowService
from django.contrib.auth import get_user_model  # Use get_user_model instead of static User import
import logging

logger = logging.getLogger(__name__)

# Function to get the user by email using the custom user model
def user_get(email):
    User = get_user_model()  # Dynamically get the custom user model
    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        return None


class PublicApi(APIView):
    authentication_classes = ()
    permission_classes = ()


class GoogleLoginRedirectApi(PublicApi):
    def get(self, request, *args, **kwargs):
        google_login_flow = GoogleRawLoginFlowService()
        authorization_url, state = google_login_flow.get_authorization_url()
        logger.debug(f"Generated state: {state}")
        request.session["google_oauth2_state"] = state
        return redirect(authorization_url)


class GoogleLoginApi(PublicApi):
    class InputSerializer(serializers.Serializer):
        code = serializers.CharField(required=False)
        error = serializers.CharField(required=False)
        state = serializers.CharField(required=False)

    def get(self, request, *args, **kwargs):
        input_serializer = self.InputSerializer(data=request.GET)
        input_serializer.is_valid(raise_exception=True)

        validated_data = input_serializer.validated_data
        code = validated_data.get("code")
        error = validated_data.get("error")
        state = validated_data.get("state")

        if error:
            logger.error(f"Google login error: {error}")
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        if not code or not state:
            logger.error("Code or state missing in Google login callback.")
            return Response(
                {"error": "Code and state are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session_state = request.session.get("google_oauth2_state")
        if not session_state or state != session_state:
            logger.error("CSRF check failed: state mismatch.")
            return Response(
                {"error": "CSRF check failed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        del request.session["google_oauth2_state"]

        google_login_flow = GoogleRawLoginFlowService()
        try:
            google_tokens = google_login_flow.get_tokens(code=code)
            user_info = google_login_flow.get_user_info(
                access_token=google_tokens["access_token"]
            )
        except Exception as e:
            logger.exception("Error during token or user info retrieval.")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        user_email = user_info["email"]
        user = user_get(user_email)  # Use the updated user_get function

        if not user:
            user = get_user_model().objects.create_user(  # Use get_user_model to create user dynamically
                username=user_email.split("@")[0],
                email=user_email,
                password=None,
            )

        login(request, user)

        return Response(
            {"user_info": user_info, "tokens": google_tokens}, status=status.HTTP_200_OK
        )
