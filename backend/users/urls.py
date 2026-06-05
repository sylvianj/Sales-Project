from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import AuthViewSet

router = DefaultRouter()
router.register(r'', AuthViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
]
