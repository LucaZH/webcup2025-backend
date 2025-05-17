from django.urls import path, re_path, include
from django.views.generic import TemplateView
from auth.views import CustomConfirmEmailView, GoogleLogin, GoogleLoginCallback

urlpatterns = [
    path("", include("dj_rest_auth.urls")),
    re_path(
    r"^registration/account-confirm-email/(?P<key>[-:\w]+)/$",
    CustomConfirmEmailView.as_view(),
    name="account_confirm_email",
    ),
    path("registration/", include("dj_rest_auth.registration.urls")),
    
    path(
        'email/confirmation/done/',
        TemplateView.as_view(template_name='account/email_confirmation_done.html'),
        name='account_email_confirmation_done'
    ),
    path("google/", GoogleLogin.as_view(), name="google_login"),
    path("google/callback/", GoogleLoginCallback.as_view(), name="google_login_callback"),
]
