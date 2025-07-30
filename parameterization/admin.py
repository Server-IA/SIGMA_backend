from django.contrib import admin
from parameterization.models import (
    City,
    Country,
    Region,
    Statues,
    StatuesCategory,
    Types,
    TypesCategory,
)

admin.site.register(City)
admin.site.register(Country)
admin.site.register(Region)
admin.site.register(Statues)
admin.site.register(StatuesCategory)
admin.site.register(Types)
admin.site.register(TypesCategory)

