from django.urls import path, include
from rest_framework import routers

from machinery.api.machinery_viewset import MachineryViewSet
from machinery.api.machinery_documentation_viewset import MachineryDocumentationViewSet

router = routers.DefaultRouter()

router.register(r'machinery', MachineryViewSet, basename='machinery')
router.register(r'machinery-documentation', MachineryDocumentationViewSet, basename='machinery-documentation')

urlpatterns = [
    path('', include(router.urls))
]