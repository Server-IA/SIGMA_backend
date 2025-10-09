from django.urls import path, include
from rest_framework import routers
from service_requests.api.customer_viewset import CustomerViewSet
from service_requests.api.person_type_viewset import PersonTypeViewSet

router = routers.DefaultRouter()

router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'person_types', PersonTypeViewSet, basename='person_type')

urlpatterns = [
    path('', include(router.urls))
]