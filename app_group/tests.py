import importlib

from django.db import migrations
from django.test import SimpleTestCase

from app_group import models as group_models

initial_migration = importlib.import_module("app_group.migrations.0001_initial")


class AppGroupModelContractTests(SimpleTestCase):
    def test_common_group_models_are_unmanaged_external_tables(self):
        expected_tables = {
            group_models.CommonGroup: 'common"."g_groups',
            group_models.CommonGroupUser: 'common"."g_group_user',
            group_models.CommonGroupJoinRequest: (
                'common"."g_group_user_ask_to_join'
            ),
        }

        for model, db_table in expected_tables.items():
            with self.subTest(model=model.__name__):
                self.assertFalse(model._meta.managed)
                self.assertEqual(model._meta.db_table, db_table)

    def test_common_membership_models_use_composite_primary_keys(self):
        self.assertEqual(
            group_models.CommonGroupUser._meta.pk.field_names,
            ("group_id", "member_id"),
        )
        self.assertEqual(
            group_models.CommonGroupJoinRequest._meta.pk.field_names,
            ("group_id", "member_id"),
        )

    def test_group_is_am_extension_without_open_mode_copy(self):
        fields = {field.name for field in group_models.Group._meta.fields}

        self.assertEqual(group_models.Group._meta.db_table, 'am"."g_group')
        self.assertIn("gg_id", fields)
        self.assertIn("celebration_retention_months", fields)
        self.assertNotIn("is_open", fields)

    def test_group_member_keeps_single_am_anchor_and_member_kinds(self):
        fields = {field.name: field for field in group_models.GroupMember._meta.fields}
        constraint_names = {
            constraint.name for constraint in group_models.GroupMember._meta.constraints
        }

        self.assertEqual(fields["ggm_id"].primary_key, True)
        self.assertEqual(fields["member"].column, "mm_id")
        self.assertEqual(fields["member"].db_constraint, False)
        self.assertEqual(
            set(dict(group_models.GroupMember.MEMBER_KIND_CHOICES)),
            {group_models.MEMBER_KIND_ACCOUNT, group_models.MEMBER_KIND_AM},
        )
        self.assertIn("g_group_member_kind_member_valid", constraint_names)
        self.assertIn("g_group_member_account_unique", constraint_names)

    def test_responsable_is_not_an_am_role_code(self):
        self.assertEqual(
            group_models.GroupRole.SYSTEM_ROLE_CODES,
            frozenset({group_models.ROLE_RESPONSABLE_IMPRESSION}),
        )
        self.assertNotIn("responsable", group_models.GroupRole.SYSTEM_ROLE_CODES)


class AppGroupMigrationContractTests(SimpleTestCase):
    def test_initial_migration_does_not_create_managed_common_tables(self):
        common_create_models = [
            operation
            for operation in initial_migration.Migration.operations
            if isinstance(operation, migrations.CreateModel)
            and operation.options.get("db_table", "").startswith('common"')
        ]

        self.assertTrue(common_create_models)
        for operation in common_create_models:
            with self.subTest(model=operation.name):
                self.assertFalse(operation.options.get("managed", True))

    def test_initial_migration_creates_only_managed_am_tables(self):
        managed_create_tables = [
            operation.options.get("db_table")
            for operation in initial_migration.Migration.operations
            if isinstance(operation, migrations.CreateModel)
            and operation.options.get("managed", True)
        ]

        self.assertTrue(managed_create_tables)
        self.assertTrue(
            all(table.startswith('am"') for table in managed_create_tables),
            managed_create_tables,
        )

    def test_initial_migration_contains_cross_schema_foreign_keys(self):
        run_sql = "\n".join(
            operation.sql
            for operation in initial_migration.Migration.operations
            if isinstance(operation, migrations.RunSQL)
        )

        expected_fragments = [
            'REFERENCES "common"."g_groups" ("group_id")',
            'REFERENCES "common"."g_group_user" ("group_id", "member_id")',
            'REFERENCES "lss"."s_songs" ("song_id")',
            'REFERENCES "lss"."s_verses" ("verse_id")',
        ]

        for fragment in expected_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, run_sql)

    def test_initial_migration_does_not_require_common_group_tags_yet(self):
        run_sql = "\n".join(
            operation.sql
            for operation in initial_migration.Migration.operations
            if isinstance(operation, migrations.RunSQL)
        )

        self.assertNotIn('REFERENCES "common"."group_tags"', run_sql)
