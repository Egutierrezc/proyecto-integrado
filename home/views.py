from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render
from rest_framework.authtoken.models import Token

from calificaciones.models import Qualification


@login_required
def index(request):
    token, _ = Token.objects.get_or_create(user=request.user)
    display_name = request.user.get_full_name() or request.user.get_username()
    visible_qualifications = Qualification.objects.visible_to(request.user)
    qualification_counts = visible_qualifications.aggregate(
        total=Count('pk'),
        broker=Count(
            'pk',
            filter=Q(origin=Qualification.Origin.BROKER),
        ),
        system=Count(
            'pk',
            filter=Q(origin=Qualification.Origin.SYSTEM),
        ),
    )
    recent_qualifications = visible_qualifications.order_by(
        '-created_at',
        '-pk',
    )[:5]
    return render(
        request,
        'home/index.html',
        {
            'api_token': token.key,
            'display_name': display_name,
            'qualification_count': qualification_counts['total'],
            'broker_qualification_count': qualification_counts['broker'],
            'system_qualification_count': qualification_counts['system'],
            'recent_qualifications': recent_qualifications,
        },
    )