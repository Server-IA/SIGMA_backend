from django.urls import path, include
from rest_framework import routers
from monitoring.views.health import health_check
from monitoring.api.data_viewset import DataViewSet

router = routers.DefaultRouter()
router.register(r'data', DataViewSet, basename='data')


urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('', include(router.urls))
]