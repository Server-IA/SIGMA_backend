from django.urls import path, include
from rest_framework import routers
from maintenance.views.maintenance_viewset import MaintenanceViewSet
from maintenance.views.maintenance_type_viewset import MaintenanceTypeViewSet

router = routers.DefaultRouter()
router.register(r'maintenance', MaintenanceViewSet, basename='maintenance')
router.register(r'maintenance-types', MaintenanceTypeViewSet, basename='maintenance-types')

urlpatterns = [
    path('', include(router.urls)),
]