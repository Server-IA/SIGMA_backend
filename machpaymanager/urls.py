from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('machinery.urls')),
    path('', include('maintenance.urls')),
    path('', include('monitoring.urls')),
    path('', include('parameterization.urls')),
    path('', include('payroll.urls')),
    path('', include('service_requests.urls')),
    path('', include('users.urls')),

]
