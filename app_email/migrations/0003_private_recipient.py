from django.db import migrations, models


def clear_invitation_addresses(apps, schema_editor):
    apps.get_model("app_email", "EmailNotification").objects.using(
        schema_editor.connection.alias
    ).filter(notification_type="group_am_member_invitation").update(recipient_email="")


class Migration(migrations.Migration):
    dependencies = [("app_email", "0002_emailnotification_sender_key_and_more")]
    operations = [
        migrations.AlterField(
            model_name="emailnotification",
            name="recipient_email",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.RunPython(clear_invitation_addresses, migrations.RunPython.noop),
    ]
