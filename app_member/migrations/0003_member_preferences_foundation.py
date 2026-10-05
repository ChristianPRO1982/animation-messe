import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app_member", "0002_preferences_roles_refactor"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    CREATE TABLE IF NOT EXISTS "am"."m_member" (
                        "mm_id" uuid NOT NULL PRIMARY KEY,
                        "is_admin" boolean NOT NULL DEFAULT false,
                        "created_at" timestamp with time zone NOT NULL DEFAULT NOW(),
                        "updated_at" timestamp with time zone NOT NULL DEFAULT NOW()
                    );

                    INSERT INTO "am"."m_member" (
                        "mm_id",
                        "is_admin",
                        "created_at",
                        "updated_at"
                    )
                    SELECT
                        source."member_id",
                        BOOL_OR(source."is_admin"),
                        NOW(),
                        NOW()
                    FROM (
                        SELECT
                            "member_id",
                            false AS "is_admin"
                        FROM "am"."m_preferences"
                        UNION ALL
                        SELECT
                            "member_id",
                            "is_admin"
                        FROM "am"."m_member_roles"
                    ) source
                    WHERE source."member_id" IS NOT NULL
                    GROUP BY source."member_id"
                    ON CONFLICT ("mm_id") DO UPDATE
                    SET
                        "is_admin" = "am"."m_member"."is_admin" OR EXCLUDED."is_admin",
                        "updated_at" = NOW();

                    ALTER TABLE "am"."m_preferences"
                    DROP CONSTRAINT IF EXISTS "m_preferences_user_fk";

                    DO $$
                    DECLARE
                        pk_name text;
                    BEGIN
                        SELECT constraint_name
                        INTO pk_name
                        FROM information_schema.table_constraints
                        WHERE table_schema = 'am'
                          AND table_name = 'm_preferences'
                          AND constraint_type = 'PRIMARY KEY'
                        LIMIT 1;

                        IF pk_name IS NOT NULL THEN
                            EXECUTE format(
                                'ALTER TABLE "am"."m_preferences" DROP CONSTRAINT %I',
                                pk_name
                            );
                        END IF;
                    END
                    $$;

                    DO $$
                    BEGIN
                        IF EXISTS (
                            SELECT 1
                            FROM information_schema.columns
                            WHERE table_schema = 'am'
                              AND table_name = 'm_preferences'
                              AND column_name = 'member_id'
                        )
                        AND NOT EXISTS (
                            SELECT 1
                            FROM information_schema.columns
                            WHERE table_schema = 'am'
                              AND table_name = 'm_preferences'
                              AND column_name = 'mm_id'
                        ) THEN
                            ALTER TABLE "am"."m_preferences"
                            RENAME COLUMN "member_id" TO "mm_id";
                        END IF;
                    END
                    $$;

                    ALTER TABLE "am"."m_preferences"
                    DROP COLUMN IF EXISTS "song_search";

                    ALTER TABLE "am"."m_preferences"
                    ADD COLUMN IF NOT EXISTS "mp_id" bigint;

                    CREATE SEQUENCE IF NOT EXISTS "am"."m_preferences_mp_id_seq";

                    ALTER SEQUENCE "am"."m_preferences_mp_id_seq"
                    OWNED BY "am"."m_preferences"."mp_id";

                    UPDATE "am"."m_preferences"
                    SET "mp_id" = nextval('"am"."m_preferences_mp_id_seq"')
                    WHERE "mp_id" IS NULL;

                    SELECT setval(
                        '"am"."m_preferences_mp_id_seq"',
                        GREATEST(
                            COALESCE((SELECT MAX("mp_id") FROM "am"."m_preferences"), 1),
                            1
                        ),
                        true
                    );

                    ALTER TABLE "am"."m_preferences"
                    ALTER COLUMN "mp_id"
                    SET DEFAULT nextval('"am"."m_preferences_mp_id_seq"');

                    ALTER TABLE "am"."m_preferences"
                    ALTER COLUMN "mp_id" SET NOT NULL;

                    ALTER TABLE "am"."m_preferences"
                    ALTER COLUMN "mm_id" SET NOT NULL;

                    ALTER TABLE "am"."m_preferences"
                    ADD COLUMN IF NOT EXISTS "calendar_week_start" varchar(8)
                    NOT NULL DEFAULT 'monday';

                    ALTER TABLE "am"."m_preferences"
                    ADD COLUMN IF NOT EXISTS "created_at" timestamp with time zone
                    NOT NULL DEFAULT NOW();

                    ALTER TABLE "am"."m_preferences"
                    ADD COLUMN IF NOT EXISTS "updated_at" timestamp with time zone
                    NOT NULL DEFAULT NOW();

                    ALTER TABLE "am"."m_preferences"
                    DROP CONSTRAINT IF EXISTS "m_preferences_pkey";

                    ALTER TABLE "am"."m_preferences"
                    ADD CONSTRAINT "m_preferences_pkey" PRIMARY KEY ("mp_id");

                    ALTER TABLE "am"."m_preferences"
                    DROP CONSTRAINT IF EXISTS "m_preferences_mm_id_key";

                    ALTER TABLE "am"."m_preferences"
                    ADD CONSTRAINT "m_preferences_mm_id_key" UNIQUE ("mm_id");

                    ALTER TABLE "am"."m_preferences"
                    DROP CONSTRAINT IF EXISTS "m_preferences_member_fk";

                    ALTER TABLE "am"."m_preferences"
                    ADD CONSTRAINT "m_preferences_member_fk"
                    FOREIGN KEY ("mm_id")
                    REFERENCES "am"."m_member" ("mm_id")
                    ON DELETE CASCADE;

                    ALTER TABLE "am"."m_preferences"
                    DROP CONSTRAINT IF EXISTS "m_preferences_calendar_week_start_valid";

                    ALTER TABLE "am"."m_preferences"
                    ADD CONSTRAINT "m_preferences_calendar_week_start_valid"
                    CHECK ("calendar_week_start" IN ('monday', 'sunday'));

                    DROP TABLE IF EXISTS "am"."m_member_roles";
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.CreateModel(
                    name="Member",
                    fields=[
                        (
                            "mm_id",
                            models.UUIDField(
                                editable=False,
                                primary_key=True,
                                serialize=False,
                            ),
                        ),
                        ("is_admin", models.BooleanField(default=False)),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                    ],
                    options={
                        "db_table": 'am"."m_member',
                    },
                ),
                migrations.RemoveConstraint(
                    model_name="memberrole",
                    name="m_member_roles_admin_requires_moderator",
                ),
                migrations.DeleteModel(
                    name="MemberRole",
                ),
                migrations.RemoveField(
                    model_name="memberpreferences",
                    name="member_id",
                ),
                migrations.RemoveField(
                    model_name="memberpreferences",
                    name="song_search",
                ),
                migrations.AddField(
                    model_name="memberpreferences",
                    name="mp_id",
                    field=models.BigAutoField(primary_key=True, serialize=False),
                ),
                migrations.AddField(
                    model_name="memberpreferences",
                    name="member",
                    field=models.OneToOneField(
                        db_column="mm_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="preferences",
                        to="app_member.member",
                    ),
                ),
                migrations.AddField(
                    model_name="memberpreferences",
                    name="calendar_week_start",
                    field=models.CharField(
                        choices=[
                            ("monday", "Lundi"),
                            ("sunday", "Dimanche"),
                        ],
                        default="monday",
                        max_length=8,
                    ),
                ),
                migrations.AddField(
                    model_name="memberpreferences",
                    name="created_at",
                    field=models.DateTimeField(auto_now_add=True),
                ),
                migrations.AddField(
                    model_name="memberpreferences",
                    name="updated_at",
                    field=models.DateTimeField(auto_now=True),
                ),
                migrations.AddConstraint(
                    model_name="memberpreferences",
                    constraint=models.CheckConstraint(
                        condition=models.Q(
                            ("calendar_week_start__in", ["monday", "sunday"])
                        ),
                        name="m_preferences_calendar_week_start_valid",
                    ),
                ),
            ],
        ),
    ]
