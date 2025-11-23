from django.urls import path, include
from rest_framework import routers
from .api.established_contract_viewset import EstablishedContractViewSet
from .api.days_of_week_viewset import DaysOfWeekViewSet
from .api.employee_viewset import EmployeeViewSet
from .api.temporary_payroll_adjustment_viewset import TemporaryPayrollAdjustmentViewSet

router = routers.DefaultRouter()
router.register(r'established_contracts', EstablishedContractViewSet, basename='established-contract')
router.register(r'days_of_week', DaysOfWeekViewSet, basename='days_of_week')
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'temporary_adjustments', TemporaryPayrollAdjustmentViewSet, basename='temporary_adjustment')

urlpatterns = [
    path('', include(router.urls))
]