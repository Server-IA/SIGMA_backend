from django.urls import path, include
from rest_framework import routers

from machinery.api.machinery_viewset import  MachineryViewSet

router = routers.DefaultRouter()

router.register(r'machinery', MachineryViewSet, basename='machinery')

urlpatterns = [
    path('', include(router.urls))
]