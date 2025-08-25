from django.contrib import admin
from parameterization.models import (
    Statues,
    StatuesCategory,
    Types,
    TypesCategory,
)

admin.site.register(Statues)
admin.site.register(StatuesCategory)
admin.site.register(Types)
admin.site.register(TypesCategory)

