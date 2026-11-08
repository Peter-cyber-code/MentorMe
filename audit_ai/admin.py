from django.contrib import admin

from .models import ProjectAudit


@admin.register(ProjectAudit)
class ProjectAuditAdmin(
    admin.ModelAdmin
):

    list_display = [
        "id",
        "project",
        "requested_by",
        "status",
        "provider",
        "created_at",
    ]

    list_filter = [
        "status",
        "provider",
        "created_at",
    ]

    search_fields = [
        "project__title",
        "requested_by__username",
    ]

    readonly_fields = [
        "report",
        "error_message",
        "created_at",
        "updated_at",
    ]