from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="EmailNotification",
            fields=[
                ("en_id", models.BigAutoField(primary_key=True, serialize=False)),
                ("notification_type", models.CharField(max_length=120)),
                ("recipient", models.EmailField(max_length=254)),
                ("group_id", models.IntegerField(blank=True, null=True)),
                ("object_type", models.CharField(blank=True, max_length=120)),
                ("object_id", models.CharField(blank=True, max_length=120)),
                (
                    "idempotency_key",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "En attente"),
                            ("sent", "Envoyé"),
                            ("failed", "Échec"),
                        ],
                        default="pending",
                        max_length=16,
                    ),
                ),
                ("provider_message_id", models.CharField(blank=True, max_length=255)),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": 'am"."email_notification',
                "ordering": ["-created_at", "-en_id"],
            },
        ),
        migrations.AddConstraint(
            model_name="emailnotification",
            constraint=models.CheckConstraint(
                condition=models.Q(("status__in", ["pending", "sent", "failed"])),
                name="email_notification_status_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="emailnotification",
            constraint=models.UniqueConstraint(
                condition=models.Q(("idempotency_key__isnull", False)),
                fields=("idempotency_key",),
                name="email_notification_idempotency_unique",
            ),
        ),
    ]
