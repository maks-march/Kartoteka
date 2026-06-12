from django.urls import path

from apps.users.views import (
    login_view, register_view, logout_view,
    profile_objects, profile_systems, profile_categories,
)

urlpatterns = [
    path("login/", login_view, name="login"),
    path("register/", register_view, name="register"),
    path("logout/", logout_view, name="logout"),
    path("profile/", profile_objects, name="profile"),
    path("profile/objects/", profile_objects, name="profile-objects"),
    path("profile/systems/", profile_systems, name="profile-systems"),
    path("profile/categories/", profile_categories, name="profile-categories"),
]
