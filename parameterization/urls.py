from django.urls import path, include
from rest_framework import routers
from parameterization.api.statues_category_viewset import StatuesCategoryViewSet
from parameterization.api.statues_viewset import StatuesViewSet
from parameterization.api.types_category_viewset import TypesCategoryViewSet
from parameterization.api.types_viewset import TypesViewSet
from parameterization.api.units_category_viewset import UnitsCategoryViewSet
from parameterization.api.units_viewset import UnitsViewSet
from parameterization.api.visual_parameterization_viewset import VisualParameterizationViewSet
from parameterization.api.user_visual_parameterization_viewset import UserVisualParameterizationViewSet
from parameterization.api.employee_departments_viewset import EmployeeDepartmentViewSet

router = routers.DefaultRouter()
router.register(r'statues_categories', StatuesCategoryViewSet, basename='statues_categories')
router.register(r'statues', StatuesViewSet, basename='statues')
router.register(r'types_categories', TypesCategoryViewSet, basename='types_categories')
router.register(r'types', TypesViewSet, basename='types')
router.register(r'units_categories', UnitsCategoryViewSet, basename='units_categories')
router.register(r'units', UnitsViewSet, basename='units')
router.register(r'visual_parameterization', VisualParameterizationViewSet, basename='visual_parameterization')
router.register(r'user_visual_parameterization', UserVisualParameterizationViewSet, basename='user_visual_parameterization')
router.register(r'employee_departments', EmployeeDepartmentViewSet, basename='employee_departments')

urlpatterns = [
    path('', include(router.urls))
]