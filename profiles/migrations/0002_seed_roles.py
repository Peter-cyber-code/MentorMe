from django.db import migrations

ROLE_CODES = [
    "project_owner",
    "mentor",
    "investor",
    "financial_expert",
    "marketing_expert",
    "legal_expert",
    "collaborator",
]


def seed_roles(apps, schema_editor):
    Role = apps.get_model("profiles", "Role")
    for code in ROLE_CODES:
        Role.objects.get_or_create(code=code)


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_roles, migrations.RunPython.noop),
    ]
