from django.urls import path, include
from rest_framework import routers

from machinery.api.machinery_tracker_sheet_viewset import MachineryTrackerViewSet
from machinery.api.machinery_viewset import  MachineryViewSet
from machinery.views.periodic_maintenance_viewset import PeriodicMaintenanceSchedulingViewSet

router = routers.DefaultRouter()

router.register(r'machinery', MachineryViewSet, basename='machinery')
router.register(r'machinery-tracker', MachineryTrackerViewSet, basename='machinery-tracker')
# Programaciones de mantenimiento periódico
router.register(
    r'machinery/periodic-maintenance',
    PeriodicMaintenanceSchedulingViewSet,
    basename='periodic-maintenance'
)
urlpatterns = [
    path('', include(router.urls))
]