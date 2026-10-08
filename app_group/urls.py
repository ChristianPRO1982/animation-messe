from django.urls import path

from app_group import views

urlpatterns = [
    path("", views.groups_home, name="groups_home"),
    path("manage/", views.groups_manage, name="groups_manage"),
    path("<int:group_id>/members/", views.group_members, name="group_members"),
    path(
        "<int:group_id>/responsables/",
        views.group_responsables,
        name="group_responsables",
    ),
    path("<int:group_id>/am-members/", views.group_am_members, name="group_am_members"),
    path("<int:group_id>/functions/", views.group_functions, name="group_functions"),
    path(
        "<int:group_id>/am-member-titles/",
        views.group_am_member_titles,
        name="group_am_member_titles",
    ),
    path("<int:group_id>/consent/", views.group_consent, name="group_consent"),
    path(
        "<int:group_id>/calendar/states/",
        views.group_calendar_states,
        name="group_calendar_states",
    ),
    path(
        "<int:group_id>/calendar/regular-rules/",
        views.group_calendar_regular_rules,
        name="group_calendar_regular_rules",
    ),
    path(
        "<int:group_id>/calendar/special-dates/",
        views.group_calendar_special_dates,
        name="group_calendar_special_dates",
    ),
    path("<int:group_id>/settings/", views.group_settings, name="group_settings"),
    path("<int:group_id>/locations/", views.group_locations, name="group_locations"),
    path("<int:group_id>/songs/", views.group_songs, name="group_songs"),
    path("<int:group_id>/", views.group_detail, name="group_detail"),
]
