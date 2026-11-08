"""
Reprend les données de l'ancien système (CustomUser.user_type / hourly_price)
vers le système unique (Profile.roles / Profile.session_price).

Note : l'ancien type EXPERT est ambigu (financier, marketing, juridique) et
n'est donc pas migré automatiquement : à affecter à la main dans l'admin.
"""
from django.db import migrations

LEGACY_TO_ROLE = {
    "PROJECT_OWNER": "project_owner",
    "MENTOR": "mentor",
    "INVESTOR": "investor",
    "COLLABORATOR": "collaborator",
}


def migrate_legacy(apps, schema_editor):
    User = apps.get_model("accounts", "CustomUser")
    Profile = apps.get_model("profiles", "Profile")
    Role = apps.get_model("profiles", "Role")

    for user in User.objects.all().iterator():
        profile, _ = Profile.objects.get_or_create(user=user)

        code = LEGACY_TO_ROLE.get(user.user_type)
        if code:
            role, _ = Role.objects.get_or_create(code=code)
            profile.roles.add(role)

        if (
            profile.session_price is None
            and user.hourly_price
            and user.hourly_price > 0
        ):
            profile.session_price = user.hourly_price
            profile.save(update_fields=["session_price"])


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
        ("profiles", "0002_seed_roles"),
    ]

    operations = [
        migrations.RunPython(migrate_legacy, migrations.RunPython.noop),
    ]
