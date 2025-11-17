from django.urls import path, include
from rest_framework import routers
from .api.established_contract_viewset import EstablishedContractViewSet

router = routers.DefaultRouter()
router.register(r'established_contracts', EstablishedContractViewSet, basename='established-contract')

urlpatterns = [
    path('', include(router.urls))
]