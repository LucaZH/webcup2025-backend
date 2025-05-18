import requests
from urllib.parse import urljoin
import requests as external_requests
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from allauth.account.views import ConfirmEmailView
from dj_rest_auth.registration.views import SocialLoginView
from google.auth.transport import requests as google_requests
from django.conf import settings
from django.urls import reverse
from django.template.response import TemplateResponse
from django.http import HttpResponseRedirect
from google.oauth2 import id_token
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from app.models import CustomUser

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = settings.GOOGLE_OAUTH_CALLBACK_URL
    client_class = OAuth2Client


class GoogleAuthCallbackView(APIView):
    def get(self, request):
        code = request.query_params.get('code')
        if not code:
            return Response({'error': 'No code provided'}, status=status.HTTP_400_BAD_REQUEST)

        token_url = 'https://oauth2.googleapis.com/token'
        data = {
            'code': code,
            'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
            'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
            'redirect_uri': settings.GOOGLE_OAUTH_CALLBACK_URL,
            'grant_type': 'authorization_code'
        }

        token_response = external_requests.post(token_url, data=data)
        if token_response.status_code != 200:
            return Response({'error': 'Failed to get token'}, status=status.HTTP_400_BAD_REQUEST)

        token_data = token_response.json()
        id_token_str = token_data.get('id_token')

        try:
            id_info = id_token.verify_oauth2_token(id_token_str, google_requests.Request(), settings.GOOGLE_CLIENT_ID)
            email = id_info['email']
            first_name = id_info.get('given_name', '')
            last_name = id_info.get('family_name', '')

            user, created = CustomUser.objects.get_or_create(email=email, defaults={
                'first_name': first_name,
                'last_name': last_name,
                'username': email 
            })

            refresh = RefreshToken.for_user(user)
            return Response({
                'email': user.email,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'message': 'Authentication successful'
            })

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CustomConfirmEmailView(ConfirmEmailView):
    template_name = 'auth/email_confirm.html'
    error_template_name = 'auth/email_confirm_error.html'

    def get_template_names(self):
        return [self.template_name]

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            context = {
                'confirmation': self.object,
                'confirm_url': request.path,
            }
        except Exception:
            context = {
                'confirmation': None,
                'confirm_url': request.path,
            }
        return TemplateResponse(request, self.get_template_names(), context)

    def post(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            self.object.confirm(request)
            return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)
        except Exception as e:
            context = {
                'error': str(e),
                'confirm_url': request.path,
            }
            return TemplateResponse(request, self.error_template_name, context)