import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app_group", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE "am"."s_song_tag"
                    ADD CONSTRAINT "s_song_tag_common_group_tag_fk"
                    FOREIGN KEY ("gt_id")
                    REFERENCES "common"."group_tags" ("gt_id")
                    ON DELETE CASCADE;
                    """,
                    reverse_sql="""
                    ALTER TABLE "am"."s_song_tag"
                    DROP CONSTRAINT IF EXISTS "s_song_tag_common_group_tag_fk";
                    """,
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name="songtag",
                    name="group_tag",
                    field=models.ForeignKey(
                        db_column="gt_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="song_tags",
                        to="app_group.commongrouptag",
                    ),
                ),
            ],
        ),
    ]
