from django.db import models


class SiteParams(models.Model):
    language = models.CharField(max_length=2, primary_key=True)
    title = models.CharField(max_length=100)
    title_h1 = models.CharField(max_length=255)
    signup_url = models.URLField(blank=True, default="")
    home_text = models.TextField()
    bloc1_text = models.TextField()
    bloc2_text = models.TextField()
    admin_message = models.TextField()
    moderator_message = models.TextField()
    admin_message_cooldown_minutes = models.IntegerField(default=5)
    moderator_message_cooldown_minutes = models.IntegerField(default=60)

    class Meta:
        db_table = 'am"."site_params'


class DirectoryUserRecord(models.Model):
    id = models.UUIDField(primary_key=True)
    username = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    enabled = models.BooleanField(default=True)
    email_verified = models.BooleanField(default=False)
    synced_at = models.DateTimeField(null=True, blank=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'users"."users'
