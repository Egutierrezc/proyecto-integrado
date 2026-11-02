from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        max_length=20,
        label='Correo electrónico',
        widget=forms.EmailInput(
            attrs={'autofocus': True, 'autocomplete': 'username', 'maxlength': '20'}
        ),
    )
    password = forms.CharField(
        max_length=20,
        label='Contraseña',
        strip=False,
        widget=forms.PasswordInput(
            attrs={'autocomplete': 'current-password', 'maxlength': '20'}
        ),
    )

    def clean_username(self):
        email = self.cleaned_data['username'].strip().lower()
        if '@' in email:
            user = User.objects.filter(email__iexact=email).only('username').first()
            if user is not None:
                return user.get_username()
        return email
