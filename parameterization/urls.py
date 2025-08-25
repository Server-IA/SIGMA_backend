from django.urls import path, include
from rest_framework import routers
from parameterization.api.statues_category_viewset import StatuesCategoryViewSet
from parameterization.api.statues_viewset import StatuesViewSet
from parameterization.api.types_category_viewset import TypesCategoryViewSet
from parameterization.api.types_viewset import TypesViewSet

router = routers.DefaultRouter()
router.register(r'statues_categories', StatuesCategoryViewSet, basename='statues_categories')
router.register(r'statues', StatuesViewSet, basename='statues')
router.register(r'types_categories', TypesCategoryViewSet, basename='types_categories')
router.register(r'types', TypesViewSet, basename='types')

urlpatterns = [
    path('', include(router.urls))
]