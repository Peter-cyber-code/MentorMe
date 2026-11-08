"""Contrôles des fichiers envoyés (images de posts, pièces jointes)."""
import os

from PIL import Image, UnidentifiedImageError
from rest_framework.exceptions import ValidationError

MB = 1024 * 1024

MAX_IMAGES = 5
MAX_IMAGE_BYTES = 5 * MB

MAX_ATTACHMENTS = 5
MAX_ATTACHMENT_BYTES = 10 * MB

# Extensions refusées en pièce jointe (exécutables, scripts, pages actives)
BLOCKED_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".com", ".msi", ".scr", ".sh", ".ps1", ".vbs",
    ".js", ".jar", ".apk", ".dll", ".html", ".htm", ".svg", ".php", ".py",
}


def validate_images(files, field="images"):
    if len(files) > MAX_IMAGES:
        raise ValidationError({field: f"Maximum {MAX_IMAGES} images par publication."})

    for f in files:
        if f.size > MAX_IMAGE_BYTES:
            raise ValidationError(
                {field: f"« {f.name} » dépasse {MAX_IMAGE_BYTES // MB} Mo."}
            )
        try:
            Image.open(f).verify()
        except (UnidentifiedImageError, OSError, SyntaxError):
            raise ValidationError({field: f"« {f.name} » n'est pas une image valide."})
        finally:
            f.seek(0)


def validate_attachments(files, field="attachments"):
    if len(files) > MAX_ATTACHMENTS:
        raise ValidationError({field: f"Maximum {MAX_ATTACHMENTS} fichiers par message."})

    for f in files:
        ext = os.path.splitext(f.name or "")[1].lower()
        if ext in BLOCKED_EXTENSIONS:
            raise ValidationError({field: f"Ce type de fichier n'est pas autorisé ({ext})."})
        if f.size > MAX_ATTACHMENT_BYTES:
            raise ValidationError(
                {field: f"« {f.name} » dépasse {MAX_ATTACHMENT_BYTES // MB} Mo."}
            )
