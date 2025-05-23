from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.apps import apps


class CustomUserAdmin(UserAdmin):
    """Define admin model for custom User model with no username field."""
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'username')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('first_name', 'username', 'email', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_superuser', 'is_staff')
    search_fields = ('email', 'username')
    ordering = ('email',)


admin.site.register(get_user_model(), CustomUserAdmin)

# app = apps.get_app_config('graphql_auth')

# for model_name, model in app.models.items():
#     admin.site.register(model)