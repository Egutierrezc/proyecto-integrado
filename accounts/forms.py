from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        max_length=50,
        label='Correo electrónico',
        widget=forms.EmailInput(
            attrs={'autofocus': True, 'autocomplete': 'username', 'maxlength': '50'}
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


class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        max_length=254,
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'placeholder': 'tu@empresa.com', 'autocomplete': 'email'})
    )

    class Meta:
        model = User
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'placeholder': 'Tu nombre de usuario', 'autocomplete': 'username'})