import uuid

from django.db import migrations, models

FALLBACK_CONSENT = """# Consentement Membre AM

J'accepte que les informations nécessaires à mon identification comme **Membre AM** soient utilisées par le groupe pour organiser l'animation des célébrations.

Ces informations sont limitées aux besoins du groupe et ne créent pas de compte de connexion.

---

Je peux demander le retrait de mon consentement auprès d'un responsable du groupe."""


def initialize_private_fields(apps, schema_editor):
    database = schema_editor.connection.alias
    for name in ("AmMember", "AmMemberRequest"):
        model = apps.get_model("app_group", name)
        for item in (
            model.objects.using(database).select_related("consent_message").iterator()
        ):
            item.public_id = uuid.uuid4()
            item.consent_body_markdown = (
                item.consent_message.body_markdown
                if item.consent_message_id
                else FALLBACK_CONSENT
            )
            item.save(
                using=database, update_fields=["public_id", "consent_body_markdown"]
            )


class Migration(migrations.Migration):
    dependencies = [
        ("app_group", "0005_group_consent_messages"),
        ("app_email", "0003_private_recipient"),
    ]
    operations = [
        migrations.RemoveField(model_name="ammemberrequest", name="email"),
        migrations.RemoveField(model_name="ammember", name="consent_email_fingerprint"),
        migrations.AddField(
            model_name="ammemberrequest",
            name="withdrawal_secret_hash",
            field=models.CharField(blank=True, max_length=255),
        ),
        *[
            operation
            for model_name in ("ammemberrequest", "ammember")
            for operation in (
                migrations.AddField(
                    model_name=model_name,
                    name="public_id",
                    field=models.UUIDField(null=True, editable=False, unique=True),
                ),
                migrations.AddField(
                    model_name=model_name,
                    name="consent_body_markdown",
                    field=models.TextField(blank=True),
                ),
            )
        ],
        migrations.RunPython(initialize_private_fields, migrations.RunPython.noop),
        *[
            migrations.AlterField(
                model_name=model_name,
                name="public_id",
                field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
            )
            for model_name in ("ammemberrequest", "ammember")
        ],
    ]
