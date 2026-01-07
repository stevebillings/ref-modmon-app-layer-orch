from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from infrastructure.django_app.models import AuditLogModel, UserProfile


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


@admin.register(AuditLogModel)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin for viewing audit logs."""

    list_display = ["event_type", "actor_id", "aggregate_type", "aggregate_id", "occurred_at"]
    list_filter = ["event_type", "aggregate_type"]
    search_fields = ["actor_id", "event_type"]
    readonly_fields = [
        "id",
        "event_type",
        "event_id",
        "occurred_at",
        "actor_id",
        "aggregate_type",
        "aggregate_id",
        "event_data",
        "created_at",
    ]
    ordering = ["-occurred_at"]
