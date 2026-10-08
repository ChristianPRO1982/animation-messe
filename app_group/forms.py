from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from app_group.models import PlanningState, SpecialDateRule


class ActionForm(forms.Form):
    action = forms.CharField(widget=forms.HiddenInput())


class ActivateGroupForm(ActionForm):
    common_group_id = forms.IntegerField(min_value=1, widget=forms.HiddenInput())


class JoinGroupRequestForm(ActionForm):
    common_group_id = forms.IntegerField(min_value=1, widget=forms.HiddenInput())


class GroupSettingsForm(ActionForm):
    celebration_retention_months = forms.IntegerField(
        label=_("Conservation des célébrations"),
        min_value=1,
        max_value=24,
        help_text=_("Durée en mois, entre 1 et 24."),
    )


class GroupMemberActionForm(ActionForm):
    group_member_id = forms.IntegerField(min_value=1, widget=forms.HiddenInput())


class CommonResponsableForm(ActionForm):
    member_id = forms.UUIDField(widget=forms.HiddenInput())
    enabled = forms.BooleanField(required=False, widget=forms.HiddenInput())


class FunctionAssignmentForm(GroupMemberActionForm):
    function_id = forms.IntegerField(min_value=1, widget=forms.HiddenInput())


class AccessRequestForm(ActionForm):
    member_id = forms.UUIDField(label=_("Membre"))
    consent_version = forms.CharField(
        label=_("Version du consentement"),
        max_length=64,
        initial="v1",
    )


class AccessRequestDecisionForm(ActionForm):
    access_request_id = forms.IntegerField(min_value=1, widget=forms.HiddenInput())


class CommonJoinRequestDecisionForm(ActionForm):
    member_id = forms.UUIDField(widget=forms.HiddenInput())


class AmMemberRequestForm(ActionForm):
    first_name = forms.CharField(label=_("Prénom"), max_length=255)
    last_name = forms.CharField(label=_("Nom"), max_length=255)
    email = forms.EmailField(label=_("Adresse e-mail"))
    consent_version = forms.CharField(
        label=_("Version du consentement"),
        max_length=64,
        initial="v1",
    )


class AmMemberRequestDecisionForm(ActionForm):
    am_member_request_id = forms.IntegerField(min_value=1, widget=forms.HiddenInput())


class AmMemberAcceptForm(AmMemberRequestDecisionForm):
    consent_token = forms.CharField(label=_("Jeton de consentement"), max_length=255)
    withdrawal_secret = forms.CharField(
        label=_("Secret personnel"),
        max_length=255,
        widget=forms.PasswordInput,
    )


class NamedGroupObjectForm(ActionForm):
    object_id = forms.IntegerField(
        min_value=1,
        required=False,
        widget=forms.HiddenInput(),
    )
    name = forms.CharField(label=_("Nom"), max_length=255)
    position = forms.IntegerField(label=_("Position"), min_value=0, initial=0)
    is_active = forms.BooleanField(label=_("Actif"), required=False, initial=True)


class GroupFunctionForm(NamedGroupObjectForm):
    auto_edit_celebration = forms.BooleanField(
        label=_("Édition automatique des célébrations"),
        required=False,
    )


class AmMemberTitleForm(ActionForm):
    object_id = forms.IntegerField(
        min_value=1,
        required=False,
        widget=forms.HiddenInput(),
    )
    label = forms.CharField(label=_("Libellé"), max_length=255)
    position = forms.IntegerField(label=_("Position"), min_value=0, initial=0)
    is_active = forms.BooleanField(label=_("Actif"), required=False, initial=True)


class GroupLocationForm(NamedGroupObjectForm):
    address = forms.CharField(
        label=_("Adresse"),
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )


class PlanningStateForm(NamedGroupObjectForm):
    color = forms.CharField(label=_("Couleur"), max_length=32, initial="#8a4b2d")
    kind = forms.ChoiceField(label=_("Type"), choices=PlanningState.KIND_CHOICES)


class CelebrationRuleForm(ActionForm):
    weekday = forms.IntegerField(label=_("Jour"), min_value=1, max_value=7)
    time = forms.TimeField(label=_("Heure"))
    location_id = forms.IntegerField(label=_("Lieu"), min_value=1)
    position = forms.IntegerField(label=_("Position"), min_value=0, initial=0)
    is_active = forms.BooleanField(label=_("Active"), required=False, initial=True)


class SpecialDateRuleForm(ActionForm):
    name = forms.CharField(label=_("Nom"), max_length=255)
    rule_type = forms.ChoiceField(
        label=_("Type"),
        choices=(
            (SpecialDateRule.RULE_ANNUAL_FIXED, _("Date annuelle fixe")),
            (SpecialDateRule.RULE_ONE_OFF, _("Date ponctuelle")),
            (SpecialDateRule.RULE_NTH_WEEKDAY, _("Nième jour du mois")),
        ),
    )
    collision_mode = forms.ChoiceField(
        label=_("Collision"),
        choices=(
            (SpecialDateRule.COLLISION_ADD, _("Ajouter")),
            (SpecialDateRule.COLLISION_REPLACE, _("Remplacer")),
        ),
    )
    month = forms.IntegerField(
        label=_("Mois"), min_value=1, max_value=12, required=False
    )
    day = forms.IntegerField(label=_("Jour"), min_value=1, max_value=31, required=False)
    exact_date = forms.DateField(label=_("Date exacte"), required=False)
    weekday = forms.IntegerField(
        label=_("Jour de semaine"),
        min_value=1,
        max_value=7,
        required=False,
    )
    occurrence = forms.IntegerField(label=_("Occurrence"), required=False)
    is_active = forms.BooleanField(label=_("Active"), required=False, initial=True)


class RepertoireSongForm(ActionForm):
    song_id = forms.IntegerField(label=_("ID chant LSS"), min_value=1)
    verse_ids = forms.CharField(
        label=_("IDs blocs LSS"),
        required=False,
        help_text=_("Séparer plusieurs IDs par des virgules ou des espaces."),
    )

    def clean_verse_ids(self) -> list[int]:
        raw_value = self.cleaned_data.get("verse_ids") or ""
        parts = [part for part in raw_value.replace(",", " ").split() if part]
        verse_ids = []
        for part in parts:
            try:
                verse_id = int(part)
            except ValueError as exc:
                raise ValidationError(
                    _("Les IDs de blocs doivent être entiers.")
                ) from exc
            if verse_id <= 0:
                raise ValidationError(_("Les IDs de blocs doivent être positifs."))
            verse_ids.append(verse_id)
        return verse_ids


class SongTagForm(ActionForm):
    song_id = forms.IntegerField(min_value=1, widget=forms.HiddenInput())
    group_tag_id = forms.IntegerField(label=_("Tag"), min_value=1)


class SongTagVerseSelectionForm(ActionForm):
    song_tag_id = forms.IntegerField(min_value=1, widget=forms.HiddenInput())
    verse_id = forms.IntegerField(min_value=1, widget=forms.HiddenInput())
    selected_by_default = forms.BooleanField(required=False, widget=forms.HiddenInput())
