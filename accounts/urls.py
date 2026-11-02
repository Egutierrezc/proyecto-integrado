from django.contrib.auth import views as auth_views
from django.urls import path

from .forms import EmailAuthenticationForm
from . import views

urlpatterns = [
    path(
        '',
        auth_views.LoginView.as_view(
            template_name='accounts/login.html',
            authentication_form=EmailAuthenticationForm,
        ),
        name='login',
    ),
    path('panel/', views.dashboard, name='dashboard'),
    path('cerrar-sesion/', auth_views.LogoutView.as_view(), name='logout'),
    path(
        'recuperar-contrasena/',
        auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset.html',
            extra_context={'reset_page': 'form'},
            email_template_name='accounts/password_reset_email.html',
            subject_template_name='accounts/password_reset_subject.txt',
            success_url='/recuperar-contrasena/enviado/',
        ),
        name='password_reset',
    ),
    path(
        'recuperar-contrasena/enviado/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset.html',
            extra_context={'reset_page': 'sent'},
        ),
        name='password_reset_done',
    ),
    path(
        'restablecer/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset.html',
            extra_context={'reset_page': 'confirm'},
            success_url='/restablecer/listo/',
        ),
        name='password_reset_confirm',
    ),
    path(
        'restablecer/listo/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset.html',
            extra_context={'reset_page': 'complete'},
        ),
        name='password_reset_complete',
    ),
]
