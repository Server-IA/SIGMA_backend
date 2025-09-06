from django.contrib import admin
from parameterization.models import (
    Statues,
    StatuesCategory,
    Types,
    TypesCategory,
    UnitsCategory,
    Units,
    VisualParameterization,
    UserVisualParameterization,
    BrandsCategory,
    Brands,
    Models,
)

admin.site.register(Statues)
admin.site.register(StatuesCategory)
admin.site.register(Types)
admin.site.register(TypesCategory)
admin.site.register(UnitsCategory)
admin.site.register(Units)
admin.site.register(VisualParameterization)
admin.site.register(UserVisualParameterization)
admin.site.register(BrandsCategory)
admin.site.register(Brands)
admin.site.register(Models)

