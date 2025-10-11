from django.urls import path, include
from rest_framework import routers
from service_requests.api.customer_viewset import CustomerViewSet
from service_requests.api.person_type_viewset import PersonTypeViewSet
from service_requests.api.service_viewset import ServiceViewSet

router = routers.DefaultRouter()

router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'person_types', PersonTypeViewSet, basename='person_type')
router.register(r'services', ServiceViewSet, basename='service')

urlpatterns = [
    path('', include(router.urls))
]