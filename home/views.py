from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from rest_framework.authtoken.models import Token


@login_required
def index(request):
    token, _ = Token.objects.get_or_create(user=request.user)
    display_name = request.user.get_full_name() or request.user.get_username()
    return render(
        request,
        'home/index.html',
        {
            'api_token': token.key,
            'display_name': display_name,
        },
    )