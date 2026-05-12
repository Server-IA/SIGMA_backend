from django.urls import path, include
from rest_framework import routers

from .api.established_contract_viewset import EstablishedContractViewSet
from .api.days_of_week_viewset import DaysOfWeekViewSet
from .api.employee_viewset import EmployeeViewSet
from .api.temporary_payroll_adjustment_viewset import TemporaryPayrollAdjustmentViewSet
from .api.employee_news_viewset import EmployeeNewsViewSet
from .api.payroll_viewset import PayrollViewSet, consult_sigma_economic_events

router = routers.DefaultRouter()

router.register(r'established_contracts', EstablishedContractViewSet, basename='established-contract')
router.register(r'days_of_week', DaysOfWeekViewSet, basename='days_of_week')
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'temporary_adjustments', TemporaryPayrollAdjustmentViewSet, basename='temporary_adjustment')
router.register(r'employee_news', EmployeeNewsViewSet, basename='employee-news')
router.register(r'payroll', PayrollViewSet, basename='payroll')

urlpatterns = [
    # RF-INT-35 - Obtención de eventos económicos de Nómina en SIGMA mediante API REST
    # GET /payroll/economic-events/consult/2025-11-01/2025-11-30/
    path(
        'payroll/economic-events/consult/<str:sincePeriod>/<str:untilPeriod>',
        consult_sigma_economic_events,
        name='sigma-payroll-economic-events-consult'
    ),

    path('', include(router.urls)),
]