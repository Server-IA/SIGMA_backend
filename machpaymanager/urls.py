from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('machinery.urls')),
    path('api/', include('maintenance.urls')),
    path('api/', include('monitoring.urls')),
    path('api/', include('parameterization.urls')),
    path('api/', include('payroll.urls')),
    path('api/', include('requests.urls')),
    path('api/', include('users.urls')),

]
