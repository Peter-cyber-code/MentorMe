from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone

from .models import CustomUser, SupportRequest

admin.site.register(CustomUser, UserAdmin)


@admin.register(SupportRequest)
class SupportRequestAdmin(admin.ModelAdmin):
    """Messages « Nous contacter » (mot de passe oublié, problème de connexion…).

    Pour aider un utilisateur qui a oublié son mot de passe :
      1. cochez sa demande puis l'action « Envoyer un code de réinitialisation » ;
      2. ou répondez-lui par e-mail, puis « Marquer comme traitée ».
    """

    list_display = ["status_badge", "email", "account", "short_message", "created_at"]
    list_display_links = ["status_badge", "email"]
    list_filter = ["status"]
    search_fields = ["email", "message", "user__first_name", "user__last_name"]
    readonly_fields = ["email", "user", "message", "created_at", "handled_by", "handled_at"]
    fields = ["email", "user", "message", "status", "admin_note", "created_at", "handled_by", "handled_at"]
    actions = ["send_reset_code", "mark_handled"]

    def get_queryset(self, request):
        from django.db.models import Case, IntegerField, Value, When

        return (
            self.model._default_manager.get_queryset()
            .select_related("user")
            .annotate(
                _rank=Case(
                    When(status="new", then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField(),
                )
            )
        )

    def get_ordering(self, request):
        return ["_rank", "-created_at"]

    @admin.display(description="Statut")
    def status_badge(self, obj):
        from django.utils.html import format_html

        color = "#b36b00" if obj.status == "new" else "#1f7a5c"
        return format_html('<b style="color:{}">{}</b>', color, obj.get_status_display())

    @admin.display(description="Compte")
    def account(self, obj):
        if not obj.user:
            return "(aucun compte avec cet e-mail)"
        return obj.user.get_full_name() or obj.user.username

    @admin.display(description="Message")
    def short_message(self, obj):
        return (obj.message[:90] + "…") if len(obj.message) > 90 else obj.message

    def save_model(self, request, obj, form, change):
        if obj.status == "handled" and not obj.handled_at:
            obj.handled_by = request.user
            obj.handled_at = timezone.now()
        super().save_model(request, obj, form, change)

    @admin.action(description="✉️ Envoyer un code de réinitialisation du mot de passe au compte")
    def send_reset_code(self, request, queryset):
        from . import password_reset as pr

        sent = 0
        for req in queryset:
            if not req.user:
                continue
            pr.send_code_email(req.user, pr.issue_code(req.user))
            req.status = "handled"
            req.handled_by = request.user
            req.handled_at = timezone.now()
            req.save()
            sent += 1
        self.message_user(request, f"{sent} code(s) envoyé(s). Ils sont valables 15 minutes.")

    @admin.action(description="✅ Marquer comme traitée")
    def mark_handled(self, request, queryset):
        updated = queryset.update(status="handled", handled_by=request.user, handled_at=timezone.now())
        self.message_user(request, f"{updated} demande(s) marquée(s) comme traitée(s).")
