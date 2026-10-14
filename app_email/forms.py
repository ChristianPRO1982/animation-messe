from django import forms
from django.utils.translation import gettext_lazy as _


class EmailSettingsForm(forms.Form):
    enabled = forms.BooleanField(
        label=_("Autoriser les envois d'e-mails"), required=False
    )
