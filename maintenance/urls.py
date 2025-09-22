from django.urls import path, include
from rest_framework import routers
from maintenance.views.maintenance_viewset import MaintenanceViewSet

router = routers.DefaultRouter()

router.register(r'maintenance', MaintenanceViewSet, basename='maintenance')

urlpatterns = [
    path('', include(router.urls))
]