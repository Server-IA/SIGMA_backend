from django.urls import path, include
from rest_framework import routers
from service_requests.api.customer_viewset import CustomerViewSet

router = routers.DefaultRouter()

router.register(r'customers', CustomerViewSet, basename='customer')

urlpatterns = [
    path('', include(router.urls))
]