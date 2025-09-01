from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('main/', include('machinery.urls')),
    path('main/', include('maintenance.urls')),
    path('main/', include('monitoring.urls')),
    path('main/', include('parameterization.urls')),
    path('main/', include('payroll.urls')),
    path('main/', include('service_requests.urls')),
    path('main/', include('users.urls')),

]
