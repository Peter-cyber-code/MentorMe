from django.contrib import admin

from .models import CallApplication, ProjectCall


@admin.register(ProjectCall)
class ProjectCallAdmin(admin.ModelAdmin):
    """Seule l'administration publie les appels à projets."""

    list_display = ["title", "organization", "category", "deadline", "is_published"]
    list_filter = ["category", "is_published"]
    search_fields = ["title", "organization", "description"]
    list_editable = ["is_published"]
    readonly_fields = ["created_by"]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CallApplication)
class CallApplicationAdmin(admin.ModelAdmin):
    """Candidatures envoyées depuis l'application (bouton « Postuler »).

    L'équipe lit la candidature et fait évoluer son statut :
    Envoyée -> Présélectionnée / Non retenue.
    """

    list_display = ["call", "user", "project", "status", "created_at"]
    list_filter = ["status", "call"]
    list_editable = ["status"]
    search_fields = ["user__username", "user__first_name", "user__last_name", "call__title", "message"]
    readonly_fields = ["call", "user", "project", "message", "created_at"]

# Les « favoris » (bouton Enregistrer) ne sont volontairement pas exposés ici :
# c'est une simple liste personnelle de chaque utilisateur.
