import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app_group", "0004_group_contract_constraints"),
    ]

    operations = [
        migrations.CreateModel(
            name="GroupConsentMessage",
            fields=[
                ("gcm_id", models.BigAutoField(primary_key=True, serialize=False)),
                ("version", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("draft", "Brouillon"), ("published", "Publie")],
                        default="draft",
                        max_length=16,
                    ),
                ),
                ("body_markdown", models.TextField()),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "group",
                    models.ForeignKey(
                        db_column="gg_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="consent_messages",
                        to="app_group.group",
                    ),
                ),
            ],
            options={
                "db_table": 'am"."g_consent_message',
                "ordering": ["-status", "-version", "-gcm_id"],
            },
        ),
        migrations.AddField(
            model_name="ammember",
            name="consent_message",
            field=models.ForeignKey(
                blank=True,
                db_column="gcm_id",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="am_members",
                to="app_group.groupconsentmessage",
            ),
        ),
        migrations.AddField(
            model_name="ammemberrequest",
            name="consent_message",
            field=models.ForeignKey(
                blank=True,
                db_column="gcm_id",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="am_member_requests",
                to="app_group.groupconsentmessage",
            ),
        ),
        migrations.AddConstraint(
            model_name="groupconsentmessage",
            constraint=models.CheckConstraint(
                condition=models.Q(("status__in", ["draft", "published"])),
                name="g_consent_message_status_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="groupconsentmessage",
            constraint=models.CheckConstraint(
                condition=models.Q(("status", "draft"), ("version__isnull", True))
                | models.Q(("status", "published"), ("version__isnull", False)),
                name="g_consent_message_version_status_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="groupconsentmessage",
            constraint=models.UniqueConstraint(
                condition=models.Q(("status", "draft")),
                fields=("group", "status"),
                name="g_consent_message_one_draft_per_group",
            ),
        ),
        migrations.AddConstraint(
            model_name="groupconsentmessage",
            constraint=models.UniqueConstraint(
                condition=models.Q(("status", "published")),
                fields=("group", "version"),
                name="g_consent_message_published_version_unique",
            ),
        ),
    ]
