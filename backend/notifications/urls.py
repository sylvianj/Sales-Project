# notifications/urls.py
from django.urls import path
from .views import notifications_list, mark_read, mark_all_read

urlpatterns = [
    path('', notifications_list, name='notifications_list'),
    path('mark-all-read/', mark_all_read, name='notifications_mark_all_read'),
    path('<int:pk>/mark-read/', mark_read, name='notifications_mark_read'),
]
