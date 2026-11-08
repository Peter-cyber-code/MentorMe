from django.conf import settings
from django.db import models

from projects.models import Project


class ProjectAudit(models.Model):

    STATUS_CHOICES = [
        ("pending", "En attente"),
        ("processing", "En cours"),
        ("completed", "Terminé"),
        ("failed", "Échec"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="audits"
    )

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_audits"
    )

    problem = models.TextField()

    solution = models.TextField()

    target_customers = models.TextField()

    business_model = models.TextField()

    competitors = models.TextField(
        blank=True
    )

    team = models.TextField(
        blank=True
    )

    funding_need = models.TextField(
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    provider = models.CharField(
        max_length=30,
        blank=True
    )

    report = models.JSONField(
        null=True,
        blank=True
    )

    error_message = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = [
            "-created_at"
        ]

    def __str__(self):

        return (
            f"Audit {self.pk} - "
            f"{self.project.title}"
        )