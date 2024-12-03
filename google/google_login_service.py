from random import SystemRandom
from urllib.parse import urlencode
from django.conf import settings
from django.urls import reverse_lazy
import requests
from django.contrib.auth import get_user_model  # Import the get_user_model function


class GoogleRawLoginFlowService:
    API_URI = reverse_lazy("google-login-callback")

    GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
    GOOGLE_ACCESS_TOKEN_OBTAIN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USER_INFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

    SCOPES = [
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "openid",
    ]

    @staticmethod
    def _generate_state_session_token(length=30):
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        rand = SystemRandom()
        return "".join(rand.choice(chars) for _ in range(length))

    def _get_redirect_uri(self):
        domain = settings.BASE_BACKEND_URL
        api_uri = "/api/google-oauth2/login/raw/callback/"
        return f"{domain}{api_uri}"

    def get_authorization_url(self):
        redirect_uri = self._get_redirect_uri()
        state = self._generate_state_session_token()

        params = {
            "response_type": "code",
            "client_id": "258049850160-5pumst1tu4k1fstq96iqc52hpa1nds5h.apps.googleusercontent.com",
            "redirect_uri": redirect_uri,
            "scope": " ".join(self.SCOPES),
            "state": state,
            "access_type": "offline",
            "include_granted_scopes": "true",
            "prompt": "select_account",
        }

        return f"{self.GOOGLE_AUTH_URL}?{urlencode(params)}", state

    def get_tokens(self, code):
        redirect_uri = self._get_redirect_uri()
        data = {
            "code": code,
            "client_id": "258049850160-5pumst1tu4k1fstq96iqc52hpa1nds5h.apps.googleusercontent.com",
            "client_secret": "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",
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        response = requests.post(self.GOOGLE_ACCESS_TOKEN_OBTAIN_URL, data=data)
        response.raise_for_status()
        return response.json()

    def get_user_info(self, access_token):
        response = requests.get(
            self.GOOGLE_USER_INFO_URL, params={"access_token": access_token}
        )
        response.raise_for_status()
        return response.json()

    # Add a method to retrieve the user based on email from the custom user model
    def get_user_by_email(self, email):
        User = get_user_model()  # Dynamically get the custom user model
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None



# "client_id": "258049850160-5pumst1tu4k1fstq96iqc52hpa1nds5h.apps.googleusercontent.com",
# "client_secret": "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",