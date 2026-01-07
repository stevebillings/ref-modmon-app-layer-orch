from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from infrastructure.django_app.models import UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile, shown on User admin page."""

    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"


class UserAdmin(BaseUserAdmin):
    """Extended User admin with UserProfile inline."""

    inlines = [UserProfileInline]


# Re-register User with the new admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Standalone admin for UserProfile."""

    list_display = ["user", "role", "created_at"]
    list_filter = ["role"]
    search_fields = ["user__username"]
    readonly_fields = ["id", "created_at"]
