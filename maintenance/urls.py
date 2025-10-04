from django.urls import path, include
from rest_framework import routers
from maintenance.api.maintenance_viewset import MaintenanceViewSet
from maintenance.api.maintenance_scheduling_viewset import MaintenanceSchedulingViewSet
from maintenance.api.maintenance_request_viewset import MaintenanceRequestViewSet
from maintenance.api.maintenance_report_viewset import MaintenanceReportViewSet

router = routers.DefaultRouter()
router.register(r'maintenance', MaintenanceViewSet, basename='maintenance')
router.register(r'maintenance_scheduling', MaintenanceSchedulingViewSet, basename='maintenance_scheduling')
router.register(r'maintenance_request', MaintenanceRequestViewSet, basename='maintenance_request')
router.register(r'maintenance_reports', MaintenanceReportViewSet, basename='maintenance_reports')

urlpatterns = [
    path('', include(router.urls)),
]