from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LogoutView
from django.shortcuts import render, redirect
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import SignUpForm


@login_required
def dashboard(request):
    token, _ = Token.objects.get_or_create(user=request.user)
    return render(
        request,
        'accounts/dashboard.html',
        {'api_token': token.key},
    )


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = SignUpForm()
        
    return render(request, 'accounts/register.html', {'form': form})


class WebLogoutView(LogoutView):
    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            Token.objects.filter(user=request.user).delete()
        return super().post(request, *args, **kwargs)


class TokenLoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        if not isinstance(request.data, dict):
            return Response(
                {'detail': 'Envía un objeto con usuario y contraseña.'},
                status=400,
            )

        username = request.data.get('username')
        password = request.data.get('password')
        if (
            not isinstance(username, str)
            or not username.strip()
            or not isinstance(password, str)
            or not password
        ):
            return Response(
                {'detail': 'El usuario y la contraseña son obligatorios.'},
                status=400,
            )

        identifier = username.strip()
        user = authenticate(
            request=request,
            username=identifier,
            password=password,
        )
        if user is None and '@' in identifier:
            account = (
                User.objects.filter(email__iexact=identifier)
                .only('username')
                .first()
            )
            if account is not None:
                user = authenticate(
                    request=request,
                    username=account.get_username(),
                    password=password,
                )

        if user is None:
            return Response(
                {'detail': 'Usuario o contraseña inválidos.'},
                status=401,
            )

        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': {
                'id': user.pk,
                'username': user.get_username(),
            },
        })


class TokenLogoutView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.auth.delete()
        return Response({'detail': 'Sesión cerrada.'})


class TokenIdentityView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'id': request.user.pk,
            'username': request.user.get_username(),
        })