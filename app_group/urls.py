from django.urls import path

from app_group import views

urlpatterns = [
    path("", views.groups_home, name="groups_home"),
    path("manage/", views.groups_manage, name="groups_manage"),
    path("<int:group_id>/", views.group_detail, name="group_detail"),
]
