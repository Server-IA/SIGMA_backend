from django.urls import path, include
from rest_framework import routers

from machinery.api.machinery_viewset import  MachineryViewSet
from machinery.api.machinery_specific_sheet_viewset import SpecificTechnicalSheetViewSet

router = routers.DefaultRouter()

router.register(r'machinery', MachineryViewSet, basename='machinery')
router.register(r'machinery-specific-sheet', SpecificTechnicalSheetViewSet, basename='machinery-specific-sheet')

urlpatterns = [
    path('', include(router.urls))
]