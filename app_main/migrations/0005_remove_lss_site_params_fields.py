from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("app_main", "0004_siteparams_signup_url"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="siteparams",
            name="verse_max_lines",
        ),
        migrations.RemoveField(
            model_name="siteparams",
            name="verse_max_characters_for_a_line",
        ),
        migrations.RemoveField(
            model_name="siteparams",
            name="chorus_prefix",
        ),
        migrations.RemoveField(
            model_name="siteparams",
            name="verse_prefix1",
        ),
        migrations.RemoveField(
            model_name="siteparams",
            name="verse_prefix2",
        ),
        migrations.RemoveField(
            model_name="siteparams",
            name="bg_img_max_bytes",
        ),
        migrations.RemoveField(
            model_name="siteparams",
            name="bg_img_min_w",
        ),
        migrations.RemoveField(
            model_name="siteparams",
            name="bg_img_min_h",
        ),
        migrations.RemoveField(
            model_name="siteparams",
            name="bg_img_max_w",
        ),
        migrations.RemoveField(
            model_name="siteparams",
            name="bg_img_max_h",
        ),
        migrations.RemoveField(
            model_name="siteparams",
            name="bg_img_ratio_min",
        ),
        migrations.RemoveField(
            model_name="siteparams",
            name="bg_img_ratio_max",
        ),
        migrations.RemoveField(
            model_name="siteparams",
            name="bg_img_allowed_ext",
        ),
        migrations.RemoveField(
            model_name="siteparams",
            name="bg_img_allowed_mime",
        ),
    ]
