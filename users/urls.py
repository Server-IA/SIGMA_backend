from django.urls import path, include
from rest_framework import routers
from users.api.person_viewset import PersonViewSet
from users.api.role_viewset import RoleViewSet

router = routers.DefaultRouter()
router.register(r'persons', PersonViewSet, basename='persons')
router.register(r'roles', RoleViewSet, basename='roles')
urlpatterns = [
    path('', include(router.urls))
]