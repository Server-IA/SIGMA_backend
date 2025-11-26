from django.urls import path, include
from rest_framework import routers
from .api.established_contract_viewset import EstablishedContractViewSet
from .api.days_of_week_viewset import DaysOfWeekViewSet
from .api.employee_viewset import EmployeeViewSet
from .api.temporary_payroll_adjustment_viewset import TemporaryPayrollAdjustmentViewSet
from .api.employee_news_viewset import EmployeeNewsViewSet
from .api.payroll_viewset import PayrollViewSet
from .api.payroll_history_report_viewset import PayrollHistoryReportViewSet

router = routers.DefaultRouter()
router.register(r'established_contracts', EstablishedContractViewSet, basename='established-contract')
router.register(r'days_of_week', DaysOfWeekViewSet, basename='days_of_week')
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'temporary_adjustments', TemporaryPayrollAdjustmentViewSet, basename='temporary_adjustment')
router.register(r'employee_news', EmployeeNewsViewSet, basename='employee-news')
router.register(r'payroll', PayrollViewSet, basename='payroll')
router.register(r'payroll_history_reports', PayrollHistoryReportViewSet, basename='payroll-history-report')

urlpatterns = [
    path('', include(router.urls))
]
