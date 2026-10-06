from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("app_member", "0003_member_preferences_foundation"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM information_schema.table_constraints
                    WHERE table_schema = 'am'
                      AND table_name = 'm_preferences'
                      AND constraint_name = 'm_users_id_not_null'
                ) THEN
                    ALTER TABLE "am"."m_preferences"
                    RENAME CONSTRAINT "m_users_id_not_null"
                    TO "m_preferences_mm_id_not_null";
                END IF;

                IF EXISTS (
                    SELECT 1
                    FROM information_schema.table_constraints
                    WHERE table_schema = 'am'
                      AND table_name = 'm_preferences'
                      AND constraint_name = 'm_users_theme_slug_not_null'
                ) THEN
                    ALTER TABLE "am"."m_preferences"
                    RENAME CONSTRAINT "m_users_theme_slug_not_null"
                    TO "m_preferences_theme_slug_not_null";
                END IF;
            END
            $$;
            """,
            reverse_sql="""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM information_schema.table_constraints
                    WHERE table_schema = 'am'
                      AND table_name = 'm_preferences'
                      AND constraint_name = 'm_preferences_mm_id_not_null'
                ) THEN
                    ALTER TABLE "am"."m_preferences"
                    RENAME CONSTRAINT "m_preferences_mm_id_not_null"
                    TO "m_users_id_not_null";
                END IF;

                IF EXISTS (
                    SELECT 1
                    FROM information_schema.table_constraints
                    WHERE table_schema = 'am'
                      AND table_name = 'm_preferences'
                      AND constraint_name = 'm_preferences_theme_slug_not_null'
                ) THEN
                    ALTER TABLE "am"."m_preferences"
                    RENAME CONSTRAINT "m_preferences_theme_slug_not_null"
                    TO "m_users_theme_slug_not_null";
                END IF;
            END
            $$;
            """,
        ),
    ]
