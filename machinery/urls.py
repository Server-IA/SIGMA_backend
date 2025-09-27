from django.urls import path, include
from rest_framework import routers

from machinery.api.machinery_tracker_sheet_viewset import MachineryTrackerViewSet
from machinery.api.machinery_viewset import MachineryViewSet
from machinery.api.machinery_specific_sheet_viewset import SpecificTechnicalSheetViewSet
from machinery.api.machinery_usage_viewset import MachineryUsageViewSet
from machinery.api.machinery_documentation_viewset import MachineryDocumentationViewSet
from machinery.api.periodic_maintenance_viewset import PeriodicMaintenanceSchedulingViewSet
from machinery.api.telemetry_devices_viewset import TelemetryDevicesViewSet

router = routers.DefaultRouter()

router.register(r'machinery', MachineryViewSet, basename='machinery')
router.register(r'machinery-tracker', MachineryTrackerViewSet, basename='machinery-tracker')
router.register(r'machinery-specific-sheet', SpecificTechnicalSheetViewSet, basename='machinery-specific-sheet')
router.register(r'machinery-usage', MachineryUsageViewSet, basename='machinery-usage')
router.register(r'machinery-documentation', MachineryDocumentationViewSet, basename='machinery-documentation')
router.register(r'periodic-maintenance', PeriodicMaintenanceSchedulingViewSet, basename='periodic-maintenance')
router.register(r'telemetry-devices', TelemetryDevicesViewSet, basename='telemetry-devices')

urlpatterns = [
    path('', include(router.urls))
]