from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app_group", "0002_song_tag_common_group_tag_fk"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name="commongrouptag",
                    name="sort_order",
                    field=models.IntegerField(default=0),
                ),
                migrations.AddField(
                    model_name="commongrouptag",
                    name="is_active",
                    field=models.BooleanField(default=True),
                ),
            ],
        ),
    ]
