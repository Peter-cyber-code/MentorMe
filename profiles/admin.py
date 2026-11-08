from django.contrib import admin
from django.utils import timezone

from notifications.models import Notification
from notifications.services import create_notification

from .models import (
    RoleRequest,
    Profile,
    Role,
    Expertise,
)


@admin.register(Profile)
class ProfileAdmin(
    admin.ModelAdmin
):

    list_display = [
        "id",
        "user",
        "country",
        "city",
        "headline",
        "is_available",
        "is_verified",
        "session_price",
    ]

    list_filter = [
        "is_available",
        "is_verified",
        "country",
        "roles",
    ]

    search_fields = [
        "user__username",
        "user__first_name",
        "user__last_name",
        "bio",
    ]

    filter_horizontal = [
        "roles",
        "expertise",
    ]


@admin.register(Role)
class RoleAdmin(
    admin.ModelAdmin
):

    list_display = [
        "id",
        "code",
    ]


@admin.register(Expertise)
class ExpertiseAdmin(
    admin.ModelAdmin
):

    list_display = [
        "id",
        "name",
    ]

    search_fields = [
        "name",
    ]

@admin.register(RoleRequest)
class RoleRequestAdmin(admin.ModelAdmin):
    """Demandes de rôle envoyées depuis l'application. Les demandes EN ATTENTE sont en haut."""

    list_display = ["status_badge", "user_name", "role", "short_message", "created_at"]
    list_display_links = ["status_badge", "user_name"]
    list_filter = ["status", "role"]
    search_fields = ["user__username", "user__first_name", "user__last_name", "message"]
    readonly_fields = ["user", "role", "profile_summary", "message", "created_at", "reviewed_by", "reviewed_at"]
    fields = ["user", "role", "profile_summary", "message", "status", "admin_note", "created_at", "reviewed_by", "reviewed_at"]
    actions = ["approve", "reject", "reapply"]

    def get_queryset(self, request):
        from django.db.models import Case, IntegerField, Value, When

        # On n'appelle pas super() : il appliquerait un tri avant que le rang existe.
        return (
            self.model._default_manager.get_queryset()
            .select_related("user", "role")
            .annotate(
                _rank=Case(
                    When(status="pending", then=Value(0)),
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

        colors = {"pending": "#b36b00", "approved": "#1f7a5c", "rejected": "#b4461f"}
        return format_html(
            '<b style="color:{}">{}</b>', colors.get(obj.status, "#444"), obj.get_status_display()
        )

    @admin.display(description="Demandeur")
    def user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    @admin.display(description="Message")
    def short_message(self, obj):
        return (obj.message[:80] + "…") if len(obj.message) > 80 else obj.message

    @admin.display(description="Profil du demandeur")
    def profile_summary(self, obj):
        from django.utils.html import format_html

        profile = getattr(obj.user, "profile", None)
        if not profile:
            return "-"
        return format_html(
            "<b>{}</b><br>{} · {} {}<br>{}<br><i>Profil complété à {} %</i>",
            obj.user.get_full_name() or obj.user.username,
            profile.headline or "(pas de titre)",
            profile.city,
            profile.country,
            profile.bio or "(pas de bio)",
            round(
                sum([
                    bool(profile.photo), bool(profile.headline.strip()), bool(profile.bio.strip()),
                    bool(profile.city.strip()), bool(profile.country.strip()), profile.expertise.exists(),
                ]) / 6 * 100
            ),
        )

    # --- application d'une décision (utilisée par les actions ET par le formulaire) ---
    def _grant(self, request, rr, notify_if_missing_only=False):
        """Rend le profil vérifié, ajoute le rôle, et prévient la personne."""
        profile = rr.user.profile
        if not profile.is_verified:
            profile.is_verified = True
            profile.save(update_fields=["is_verified"])
        profile.roles.add(rr.role)

        already_notified = Notification.objects.filter(
            recipient=rr.user,
            notification_type="role_approved",
            resource_type="role_request",
            resource_id=rr.id,
        ).exists()
        if not (notify_if_missing_only and already_notified):
            create_notification(
                recipient=rr.user,
                sender=request.user,
                notification_type="role_approved",
                title="Votre demande est validée",
                message=f"Vous êtes désormais : {rr.role.get_code_display()}.",
                resource_type="role_request",
                resource_id=rr.id,
            )

    def _decline(self, request, rr):
        create_notification(
            recipient=rr.user,
            sender=request.user,
            notification_type="role_rejected",
            title="Votre demande n'a pas été retenue",
            message=rr.admin_note or "Complétez votre profil et réessayez.",
            resource_type="role_request",
            resource_id=rr.id,
        )

    def save_model(self, request, obj, form, change):
        """Si l'admin change le statut dans le formulaire, la décision est appliquée."""
        previous = None
        if change:
            previous = RoleRequest.objects.filter(pk=obj.pk).values_list("status", flat=True).first()

        if obj.status != "pending" and obj.status != previous:
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()

        super().save_model(request, obj, form, change)

        if obj.status != previous:
            if obj.status == "approved":
                self._grant(request, obj)
                self.message_user(request, f"{obj.user} est maintenant : {obj.role.get_code_display()}.")
            elif obj.status == "rejected":
                self._decline(request, obj)

    @admin.action(description="✅ Valider les demandes sélectionnées (le profil devient vérifié)")
    def approve(self, request, queryset):
        count = 0
        for rr in queryset.filter(status="pending"):
            rr.status = "approved"
            rr.reviewed_by = request.user
            rr.reviewed_at = timezone.now()
            rr.save()
            self._grant(request, rr)
            count += 1
        self.message_user(request, f"{count} demande(s) validée(s).")

    @admin.action(description="❌ Refuser les demandes sélectionnées")
    def reject(self, request, queryset):
        count = 0
        for rr in queryset.filter(status="pending"):
            rr.status = "rejected"
            rr.reviewed_by = request.user
            rr.reviewed_at = timezone.now()
            rr.save()
            self._decline(request, rr)
            count += 1
        self.message_user(request, f"{count} demande(s) refusée(s).")

    @admin.action(description="🔁 Réappliquer la validation (corrige une demande passée en « Validée » sans effet)")
    def reapply(self, request, queryset):
        count = 0
        for rr in queryset.filter(status="approved"):
            self._grant(request, rr, notify_if_missing_only=True)
            count += 1
        self.message_user(request, f"{count} validation(s) réappliquée(s) : rôle ajouté et personne prévenue.")


# ---- Bandeau « À traiter » sur la page d'accueil de l'admin -------------------
_original_index = admin.site.index


def _index_with_pending(request, extra_context=None):
    from calls.models import CallApplication

    extra_context = extra_context or {}
    extra_context["pending_role_requests"] = RoleRequest.objects.filter(status="pending").count()
    extra_context["pending_call_applications"] = CallApplication.objects.filter(status="submitted").count()
    from accounts.models import SupportRequest

    extra_context["pending_support"] = SupportRequest.objects.filter(status="new").count()
    return _original_index(request, extra_context)


admin.site.index = _index_with_pending
