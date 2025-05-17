import requests
from urllib.parse import urljoin

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from allauth.account.views import ConfirmEmailView
from dj_rest_auth.registration.views import SocialLoginView

from django.conf import settings
from django.urls import reverse
from django.template.response import TemplateResponse
from django.http import HttpResponseRedirect

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = settings.GOOGLE_OAUTH_CALLBACK_URL
    client_class = OAuth2Client


class GoogleLoginCallback(APIView):
    def get(self, request, *args, **kwargs):
        code = request.GET.get("code")
        if code is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        token_endpoint_url = urljoin(settings.BACKEND_HOST, reverse("google_login"))
        response = requests.post(url=token_endpoint_url, data={"code": code})

        return Response(response.json(), status=status.HTTP_200_OK)


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