from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

SONG_SEARCH_VALIDATION_VALUES = {
    "all",
    "validated_only",
    "non_validated_only",
}


def default_song_search() -> dict[str, object]:
    return {
        "text": "",
        "everywhere": False,
        "match_all_selected_refs": False,
        "genre_ids": [],
        "band_ids": [],
        "artist_ids": [],
        "validation": "all",
        "favorites_only": False,
    }


def validate_song_search(value: object) -> None:
    """Legacy migration helper for the retired LSS song_search field."""
    if not isinstance(value, dict):
        raise ValidationError(_("song_search doit être un objet JSON."))

    expected_keys = {
        "text",
        "everywhere",
        "match_all_selected_refs",
        "genre_ids",
        "band_ids",
        "artist_ids",
        "validation",
        "favorites_only",
    }
    unexpected_keys = set(value) - expected_keys
    if unexpected_keys:
        raise ValidationError(
            _("song_search contient des clés non prises en charge : %(keys)s.")
            % {"keys": ", ".join(sorted(unexpected_keys))}
        )

    if not isinstance(value.get("text", ""), str):
        raise ValidationError(_("song_search.text doit être une chaîne de caractères."))

    for key in ("everywhere", "match_all_selected_refs", "favorites_only"):
        if not isinstance(value.get(key), bool):
            raise ValidationError(
                _("song_search.%(key)s doit être un booléen.") % {"key": key}
            )

    for key in ("genre_ids", "band_ids", "artist_ids"):
        ids = value.get(key)
        if not isinstance(ids, list):
            raise ValidationError(
                _("song_search.%(key)s doit être une liste.") % {"key": key}
            )
        if not all(isinstance(item, int) for item in ids):
            raise ValidationError(
                _(
                    "song_search.%(key)s doit contenir uniquement des identifiants entiers."
                )
                % {"key": key}
            )

    validation = value.get("validation")
    if validation not in SONG_SEARCH_VALIDATION_VALUES:
        raise ValidationError(
            _(
                "song_search.validation doit être l'une des valeurs suivantes : all, validated_only, non_validated_only."
            )
        )


class Member(models.Model):
    mm_id = models.UUIDField(primary_key=True, editable=False)
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'am"."m_member'


class MemberPreferences(models.Model):
    CALENDAR_WEEK_START_MONDAY = "monday"
    CALENDAR_WEEK_START_SUNDAY = "sunday"
    CALENDAR_WEEK_START_CHOICES = (
        (CALENDAR_WEEK_START_MONDAY, _("Lundi")),
        (CALENDAR_WEEK_START_SUNDAY, _("Dimanche")),
    )

    mp_id = models.BigAutoField(primary_key=True)
    member = models.OneToOneField(
        Member,
        on_delete=models.CASCADE,
        db_column="mm_id",
        related_name="preferences",
    )
    theme_slug = models.CharField(max_length=32, default="normal")
    calendar_week_start = models.CharField(
        max_length=8,
        choices=CALENDAR_WEEK_START_CHOICES,
        default=CALENDAR_WEEK_START_MONDAY,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'am"."m_preferences'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    calendar_week_start__in=[
                        "monday",
                        "sunday",
                    ]
                ),
                name="m_preferences_calendar_week_start_valid",
            ),
        ]
