from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app_group", "0003_common_group_tag_runtime_fields"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="celebrationrule",
            constraint=models.CheckConstraint(
                condition=models.Q(("weekday__gte", 1), ("weekday__lte", 7)),
                name="g_celebration_rule_weekday_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="celebrationrule",
            constraint=models.UniqueConstraint(
                condition=models.Q(("is_active", True)),
                fields=("group", "weekday", "time", "location"),
                name="g_celebration_rule_active_slot_unique",
            ),
        ),
        migrations.AddConstraint(
            model_name="specialdaterule",
            constraint=models.CheckConstraint(
                condition=models.Q(("month__isnull", True))
                | models.Q(("month__gte", 1), ("month__lte", 12)),
                name="g_special_date_rule_month_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="specialdaterule",
            constraint=models.CheckConstraint(
                condition=models.Q(("day__isnull", True))
                | models.Q(("day__gte", 1), ("day__lte", 31)),
                name="g_special_date_rule_day_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="specialdaterule",
            constraint=models.CheckConstraint(
                condition=models.Q(("weekday__isnull", True))
                | models.Q(("weekday__gte", 1), ("weekday__lte", 7)),
                name="g_special_date_rule_weekday_valid",
            ),
        ),
    ]
