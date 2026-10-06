from django.shortcuts import render


def groups_home(request):
    return render(request, "app_group/groups_home.html")
