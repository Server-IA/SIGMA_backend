from django.urls import path, include
from rest_framework import routers
from monitoring.views.health import health_check

router = routers.DefaultRouter()

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('', include(router.urls))
]