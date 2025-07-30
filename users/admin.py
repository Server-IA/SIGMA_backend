from django.contrib import admin
from users.models import (
    Person,
    User,
    Role,
    UsersRoles
)

admin.site.register(Person)
admin.site.register(User)
admin.site.register(Role)
admin.site.register(UsersRoles)