# notifications/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Notification


def _data(n):
    return {
        'id': n.id,
        'title': n.subject,
        'message': n.message,
        'channel': n.sent_via,
        'severity': 'info',
        'is_read': n.is_read,
        'created_at': n.sent_at,
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notifications_list(request):
    qs = Notification.objects.all().order_by('-sent_at')
    if request.GET.get('is_read') == 'false':
        qs = qs.filter(is_read=False)
    return Response([_data(n) for n in qs[:100]])


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_read(request, pk):
    Notification.objects.filter(pk=pk).update(is_read=True)
    return Response({'success': True})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_read(request):
    Notification.objects.filter(is_read=False).update(is_read=True)
    return Response({'success': True})
