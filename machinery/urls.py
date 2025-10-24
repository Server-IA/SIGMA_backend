from django.urls import path, include
from rest_framework import routers

from machinery.api.machinery_tracker_sheet_viewset import MachineryTrackerViewSet
from machinery.api.machinery_viewset import MachineryViewSet
from machinery.api.machinery_specific_sheet_viewset import SpecificTechnicalSheetViewSet
from machinery.api.machinery_usage_viewset import MachineryUsageViewSet
from machinery.api.machinery_documentation_viewset import MachineryDocumentationViewSet
from machinery.api.periodic_maintenance_viewset import PeriodicMaintenanceSchedulingViewSet
from machinery.api.telemetry_devices_viewset import TelemetryDevicesViewSet
from machinery.api.parameters_viewset import ParametersViewSet
from machinery.api.machinery_tolerance_thresholds_viewset import MachineryToleranceThresholdsViewSet
from machinery.api.obd_faults_viewset import OBDFaultsViewSet
from machinery.api.event_types_viewset import EventTypesViewSet

router = routers.DefaultRouter()

router.register(r'machinery', MachineryViewSet, basename='machinery')
router.register(r'machinery-tracker', MachineryTrackerViewSet, basename='machinery-tracker')
router.register(r'machinery-specific-sheet', SpecificTechnicalSheetViewSet, basename='machinery-specific-sheet')
router.register(r'machinery-usage', MachineryUsageViewSet, basename='machinery-usage')
router.register(r'machinery-documentation', MachineryDocumentationViewSet, basename='machinery-documentation')
router.register(r'periodic-maintenance', PeriodicMaintenanceSchedulingViewSet, basename='periodic-maintenance')
router.register(r'telemetry-devices', TelemetryDevicesViewSet, basename='telemetry-devices')
router.register(r'parameters', ParametersViewSet, basename='parameters')
router.register(r'tolerance-thresholds', MachineryToleranceThresholdsViewSet, basename='tolerance-thresholds')
router.register(r'obd-faults', OBDFaultsViewSet, basename='obd-faults')
router.register(r'event-types', EventTypesViewSet, basename='event-types')

urlpatterns = [
    path('', include(router.urls))
]