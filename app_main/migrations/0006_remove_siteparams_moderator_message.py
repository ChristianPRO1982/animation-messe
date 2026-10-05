from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("app_main", "0005_remove_lss_site_params_fields"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="siteparams",
            name="moderator_message",
        ),
        migrations.RemoveField(
            model_name="siteparams",
            name="moderator_message_cooldown_minutes",
        ),
    ]
