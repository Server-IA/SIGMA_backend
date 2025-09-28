from django.urls import path, include
from rest_framework import routers
from maintenance.api.maintenance_viewset import MaintenanceViewSet
from maintenance.api.maintenance_scheduling_viewset import MaintenanceSchedulingViewSet

router = routers.DefaultRouter()
router.register(r'maintenance', MaintenanceViewSet, basename='maintenance')
router.register(r'maintenance_scheduling', MaintenanceSchedulingViewSet, basename='maintenance_scheduling')

urlpatterns = [
    path('', include(router.urls)),
]