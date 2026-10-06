from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower, Trim
from django.utils.translation import gettext_lazy as _

from app_member.models import Member

MEMBER_KIND_ACCOUNT = "account"
MEMBER_KIND_AM = "am"
ROLE_RESPONSABLE_IMPRESSION = "responsable_impression"
REQUEST_TYPE_AM_ACCESS = "am_access"
PLANNING_STATE_SELECTION = "selection"
PLANNING_STATE_DEFAULT = "default"


class CommonGroup(models.Model):
    STATUS_OPEN = "open"
    STATUS_PRIVATE = "private"
    STATUS_CHOICES = (
        (STATUS_OPEN, _("Ouvert")),
        (STATUS_PRIVATE, _("Prive")),
    )

    group_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    info = models.TextField(blank=True, null=True)
    secret_ciphertext = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default=STATUS_OPEN,
    )

    class Meta:
        managed = False
        db_table = 'common"."g_groups'


class CommonGroupUser(models.Model):
    pk = models.CompositePrimaryKey("group_id", "member_id")
    group_id = models.IntegerField()
    member_id = models.UUIDField()
    is_group_admin = models.BooleanField(default=False)
    am_access = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = 'common"."g_group_user'


class CommonGroupJoinRequest(models.Model):
    pk = models.CompositePrimaryKey("group_id", "member_id")
    group_id = models.IntegerField()
    member_id = models.UUIDField()

    class Meta:
        managed = False
        db_table = 'common"."g_group_user_ask_to_join'


class CommonGroupTag(models.Model):
    gt_id = models.BigIntegerField(primary_key=True)
    group_id = models.IntegerField()
    name = models.CharField(max_length=255)
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = 'common"."group_tags'


class Group(models.Model):
    gg_id = models.IntegerField(primary_key=True)
    celebration_retention_months = models.PositiveSmallIntegerField(default=24)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'am"."g_group'
        constraints = [
            models.CheckConstraint(
                condition=Q(
                    celebration_retention_months__gte=1,
                    celebration_retention_months__lte=24,
                ),
                name="g_group_retention_months_valid",
            ),
        ]


class GroupMember(models.Model):
    MEMBER_KIND_CHOICES = (
        (MEMBER_KIND_ACCOUNT, _("Compte")),
        (MEMBER_KIND_AM, _("Membre AM")),
    )

    ggm_id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        db_column="gg_id",
        related_name="members",
    )
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        db_column="mm_id",
        related_name="group_memberships",
        blank=True,
        null=True,
        db_constraint=False,
    )
    member_kind = models.CharField(max_length=16, choices=MEMBER_KIND_CHOICES)
    joined_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'am"."g_group_member'
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(member_kind=MEMBER_KIND_ACCOUNT, member__isnull=False)
                    | Q(member_kind=MEMBER_KIND_AM, member__isnull=True)
                ),
                name="g_group_member_kind_member_valid",
            ),
            models.UniqueConstraint(
                fields=["group", "member"],
                condition=Q(
                    member_kind=MEMBER_KIND_ACCOUNT,
                    member__isnull=False,
                ),
                name="g_group_member_account_unique",
            ),
        ]


class AmMemberTitle(models.Model):
    gamt_id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        db_column="gg_id",
        related_name="am_member_titles",
    )
    label = models.CharField(max_length=255)
    position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'am"."g_am_member_title'
        ordering = ["position", "gamt_id"]


class AmMember(models.Model):
    gam_id = models.BigAutoField(primary_key=True)
    group_member = models.OneToOneField(
        GroupMember,
        on_delete=models.CASCADE,
        db_column="ggm_id",
        related_name="am_profile",
    )
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    title = models.ForeignKey(
        AmMemberTitle,
        on_delete=models.SET_NULL,
        db_column="gamt_id",
        related_name="am_members",
        blank=True,
        null=True,
    )
    consented_at = models.DateTimeField()
    consent_version = models.CharField(max_length=64)
    consent_email_fingerprint = models.CharField(max_length=255)
    withdrawal_secret_hash = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'am"."g_am_member'


class GroupRole(models.Model):
    SYSTEM_ROLE_CODES = frozenset({ROLE_RESPONSABLE_IMPRESSION})

    gr_id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        db_column="gg_id",
        related_name="roles",
    )
    code = models.CharField(max_length=64)
    label = models.CharField(max_length=255)
    position = models.PositiveIntegerField(default=0)
    is_system = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'am"."g_role'
        constraints = [
            models.UniqueConstraint(
                fields=["group", "code"],
                name="g_role_group_code_unique",
            ),
        ]
        ordering = ["position", "gr_id"]


class GroupMemberRole(models.Model):
    ggmr_id = models.BigAutoField(primary_key=True)
    group_member = models.ForeignKey(
        GroupMember,
        on_delete=models.CASCADE,
        db_column="ggm_id",
        related_name="role_assignments",
    )
    role = models.ForeignKey(
        GroupRole,
        on_delete=models.CASCADE,
        db_column="gr_id",
        related_name="member_assignments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'am"."g_group_member_role'
        constraints = [
            models.UniqueConstraint(
                fields=["group_member", "role"],
                name="g_group_member_role_unique",
            ),
        ]


class GroupFunction(models.Model):
    gf_id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        db_column="gg_id",
        related_name="functions",
    )
    name = models.CharField(max_length=255)
    position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    auto_edit_celebration = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'am"."g_function'
        constraints = [
            models.UniqueConstraint(
                Lower(Trim("name")),
                "group",
                name="g_function_group_name_unique",
            ),
        ]
        ordering = ["position", "gf_id"]


class GroupMemberFunction(models.Model):
    ggmf_id = models.BigAutoField(primary_key=True)
    group_member = models.ForeignKey(
        GroupMember,
        on_delete=models.CASCADE,
        db_column="ggm_id",
        related_name="function_assignments",
    )
    function = models.ForeignKey(
        GroupFunction,
        on_delete=models.CASCADE,
        db_column="gf_id",
        related_name="member_assignments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'am"."g_group_member_function'
        constraints = [
            models.UniqueConstraint(
                fields=["group_member", "function"],
                name="g_group_member_function_unique",
            ),
        ]


class GroupLocation(models.Model):
    gl_id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        db_column="gg_id",
        related_name="locations",
    )
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True)
    position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'am"."g_location'
        ordering = ["position", "gl_id"]


class AccessRequest(models.Model):
    REQUEST_TYPE_CHOICES = ((REQUEST_TYPE_AM_ACCESS, _("Acces AM")),)

    gar_id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        db_column="gg_id",
        related_name="access_requests",
    )
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        db_column="mm_id",
        related_name="group_access_requests",
        db_constraint=False,
    )
    request_type = models.CharField(
        max_length=16,
        choices=REQUEST_TYPE_CHOICES,
        default=REQUEST_TYPE_AM_ACCESS,
    )
    consented_at = models.DateTimeField(blank=True, null=True)
    consent_version = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'am"."g_access_request'
        constraints = [
            models.CheckConstraint(
                condition=Q(request_type=REQUEST_TYPE_AM_ACCESS),
                name="g_access_request_type_valid",
            ),
            models.UniqueConstraint(
                fields=["group", "member", "request_type"],
                name="g_access_request_active_unique",
            ),
        ]


class AmMemberRequest(models.Model):
    STATUS_PENDING = "pending"
    STATUS_REFUSED = "refused"
    STATUS_EXPIRED = "expired"
    STATUS_CHOICES = (
        (STATUS_PENDING, _("En attente")),
        (STATUS_REFUSED, _("Refusee")),
        (STATUS_EXPIRED, _("Expiree")),
    )

    gamr_id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        db_column="gg_id",
        related_name="am_member_requests",
    )
    requested_by = models.ForeignKey(
        GroupMember,
        on_delete=models.SET_NULL,
        db_column="requested_by_ggm_id",
        related_name="requested_am_members",
        blank=True,
        null=True,
    )
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    consent_token_hash = models.CharField(max_length=255)
    consent_version = models.CharField(max_length=64)
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    expires_at = models.DateTimeField()
    refused_at = models.DateTimeField(blank=True, null=True)
    display_hint = models.CharField(max_length=255, blank=True)
    purge_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'am"."g_am_member_request'


class PlanningState(models.Model):
    KIND_SELECTION = PLANNING_STATE_SELECTION
    KIND_DEFAULT = PLANNING_STATE_DEFAULT
    KIND_CUSTOM = "custom"
    KIND_CHOICES = (
        (KIND_SELECTION, _("Selection")),
        (KIND_DEFAULT, _("Defaut")),
        (KIND_CUSTOM, _("Personnalise")),
    )

    gps_id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        db_column="gg_id",
        related_name="planning_states",
    )
    name = models.CharField(max_length=255)
    color = models.CharField(max_length=32)
    kind = models.CharField(max_length=16, choices=KIND_CHOICES)
    position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'am"."g_planning_state'
        constraints = [
            models.CheckConstraint(
                condition=Q(
                    kind__in=[
                        PLANNING_STATE_SELECTION,
                        PLANNING_STATE_DEFAULT,
                        "custom",
                    ]
                ),
                name="g_planning_state_kind_valid",
            ),
            models.UniqueConstraint(
                fields=["group", "kind"],
                condition=Q(kind=PLANNING_STATE_SELECTION, is_active=True),
                name="g_planning_state_active_selection_unique",
            ),
            models.UniqueConstraint(
                fields=["group", "kind"],
                condition=Q(kind=PLANNING_STATE_DEFAULT, is_active=True),
                name="g_planning_state_active_default_unique",
            ),
        ]
        ordering = ["position", "gps_id"]


class CelebrationRule(models.Model):
    gcr_id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        db_column="gg_id",
        related_name="celebration_rules",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        db_column="parent_gcr_id",
        related_name="linked_rules",
        blank=True,
        null=True,
    )
    weekday = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    time = models.TimeField()
    location = models.ForeignKey(
        GroupLocation,
        on_delete=models.PROTECT,
        db_column="gl_id",
        related_name="celebration_rules",
    )
    position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'am"."g_celebration_rule'
        ordering = ["position", "gcr_id"]


class SpecialDateRule(models.Model):
    RULE_ANNUAL_FIXED = "annual_fixed"
    RULE_ONE_OFF = "one_off"
    RULE_NTH_WEEKDAY = "nth_weekday"
    COLLISION_ADD = "add"
    COLLISION_REPLACE = "replace"

    gsdr_id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        db_column="gg_id",
        related_name="special_date_rules",
    )
    name = models.CharField(max_length=255)
    rule_type = models.CharField(max_length=32)
    collision_mode = models.CharField(max_length=16)
    month = models.PositiveSmallIntegerField(blank=True, null=True)
    day = models.PositiveSmallIntegerField(blank=True, null=True)
    exact_date = models.DateField(blank=True, null=True)
    weekday = models.PositiveSmallIntegerField(blank=True, null=True)
    occurrence = models.SmallIntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'am"."g_special_date_rule'
        constraints = [
            models.CheckConstraint(
                condition=Q(
                    rule_type__in=[
                        "annual_fixed",
                        "one_off",
                        "nth_weekday",
                    ]
                ),
                name="g_special_date_rule_type_valid",
            ),
            models.CheckConstraint(
                condition=Q(collision_mode__in=["add", "replace"]),
                name="g_special_date_rule_collision_valid",
            ),
        ]


class SpecialDateCelebration(models.Model):
    gsdc_id = models.BigAutoField(primary_key=True)
    special_date_rule = models.ForeignKey(
        SpecialDateRule,
        on_delete=models.CASCADE,
        db_column="gsdr_id",
        related_name="celebrations",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        db_column="parent_gsdc_id",
        related_name="linked_celebrations",
        blank=True,
        null=True,
    )
    time = models.TimeField()
    location = models.ForeignKey(
        GroupLocation,
        on_delete=models.PROTECT,
        db_column="gl_id",
        related_name="special_date_celebrations",
    )
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'am"."g_special_date_celebration'
        ordering = ["position", "gsdc_id"]


class Song(models.Model):
    ss_id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        db_column="gg_id",
        related_name="songs",
    )
    song_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'am"."s_song'
        constraints = [
            models.UniqueConstraint(
                fields=["group", "song_id"],
                name="s_song_group_song_unique",
            ),
        ]


class Verse(models.Model):
    sv_id = models.BigAutoField(primary_key=True)
    song = models.ForeignKey(
        Song,
        on_delete=models.CASCADE,
        db_column="ss_id",
        related_name="verses",
    )
    verse_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'am"."s_verse'
        constraints = [
            models.UniqueConstraint(
                fields=["song", "verse_id"],
                name="s_verse_song_verse_unique",
            ),
        ]


class SongTag(models.Model):
    sst_id = models.BigAutoField(primary_key=True)
    song = models.ForeignKey(
        Song,
        on_delete=models.CASCADE,
        db_column="ss_id",
        related_name="song_tags",
    )
    group_tag = models.ForeignKey(
        CommonGroupTag,
        on_delete=models.CASCADE,
        db_column="gt_id",
        related_name="song_tags",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'am"."s_song_tag'
        constraints = [
            models.UniqueConstraint(
                fields=["song", "group_tag"],
                name="s_song_tag_unique",
            ),
        ]


class SongTagVerse(models.Model):
    sstv_id = models.BigAutoField(primary_key=True)
    song_tag = models.ForeignKey(
        SongTag,
        on_delete=models.CASCADE,
        db_column="sst_id",
        related_name="verse_selections",
    )
    verse = models.ForeignKey(
        Verse,
        on_delete=models.CASCADE,
        db_column="sv_id",
        related_name="tag_selections",
    )
    selected_by_default = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'am"."s_song_tag_verse'
        constraints = [
            models.UniqueConstraint(
                fields=["song_tag", "verse"],
                name="s_song_tag_verse_unique",
            ),
        ]
