from django.urls import path, include
from rest_framework import routers
from .api.established_contract_viewset import EstablishedContractViewSet
from .api.days_of_week_viewset import DaysOfWeekViewSet
from .api.employee_viewset import EmployeeViewSet
from .api.temporary_payroll_adjustment_viewset import TemporaryPayrollAdjustmentViewSet
from .api.employee_news_viewset import EmployeeNewsViewSet
from .api.payroll_information_viewset import PayrollInformationViewSet

router = routers.DefaultRouter()
router.register(r'established_contracts', EstablishedContractViewSet, basename='established-contract')
router.register(r'days_of_week', DaysOfWeekViewSet, basename='days_of_week')
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'temporary_adjustments', TemporaryPayrollAdjustmentViewSet, basename='temporary_adjustment')
router.register(r'employee_news', EmployeeNewsViewSet, basename='employee-news')
router.register(r'payroll-information', PayrollInformationViewSet, basename='payroll-information')

urlpatterns = [
    path('', include(router.urls))
]