from django.urls import path, include
from rest_framework import routers
from .api.established_contract_viewset import EstablishedContractViewSet
from .api.days_of_week_viewset import DaysOfWeekViewSet
from .api.employee_viewset import EmployeeViewSet
from .api.temporary_payroll_adjustment_viewset import TemporaryPayrollAdjustmentViewSet
from .api.employee_news_viewset import EmployeeNewsViewSet
<<<<<<< HEAD
from .api.payroll_history_report_viewset import PayrollHistoryReportViewSet
=======
from .api.payroll_viewset import PayrollViewSet
>>>>>>> 52f5d71aed5d27ab18065c6c740db3c2d4af4941

router = routers.DefaultRouter()
router.register(r'established_contracts', EstablishedContractViewSet, basename='established-contract')
router.register(r'days_of_week', DaysOfWeekViewSet, basename='days_of_week')
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'temporary_adjustments', TemporaryPayrollAdjustmentViewSet, basename='temporary_adjustment')
router.register(r'employee_news', EmployeeNewsViewSet, basename='employee-news')
<<<<<<< HEAD
router.register(r'payroll_history_reports', PayrollHistoryReportViewSet, basename='payroll-history-report')
=======
router.register(r'payroll', PayrollViewSet, basename='payroll')
>>>>>>> 52f5d71aed5d27ab18065c6c740db3c2d4af4941

urlpatterns = [
    path('', include(router.urls))
]