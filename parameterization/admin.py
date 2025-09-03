from django.contrib import admin
from parameterization.models import (
    Statues,
    StatuesCategory,
    Types,
    TypesCategory,
    UnitsCategory,
    Units,
)

admin.site.register(Statues)
admin.site.register(StatuesCategory)
admin.site.register(Types)
admin.site.register(TypesCategory)
admin.site.register(UnitsCategory)
admin.site.register(Units)

