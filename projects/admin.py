from django.contrib import admin
from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):

    list_display = [
        "id",
        "title",
        "sector",
        "owner",
        "stage",
        "created_at",
    ]

    search_fields = [
        "title",
        "sector",
        "country",
    ]

    list_filter = [
        "stage",
        "sector",
        "country",
    ]