from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from apps.users.usecases.usecase import AuthUseCase
from apps.objects.usecases.object_usecase import ObjectUseCase
from apps.system.usecases.system_usecase import SystemUseCase


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("profile")

    error = None
    if request.method == "POST":
        usecase = AuthUseCase()
        try:
            user = usecase.login(
                username=request.POST.get("username"),
                password=request.POST.get("password"),
            )
            login(request, user)  # создает сессию в cookie
            return redirect("profile")
        except Exception as e:
            error = e.message

    return render(request, "users/login.html", {"error": error})


@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.user.is_authenticated:
        return redirect("profile")

    error = None
    if request.method == "POST":
        usecase = AuthUseCase()
        try:
            user = usecase.register(
                username=request.POST.get("username"),
                password=request.POST.get("password"),
            )
            login(request, user)  # сразу логиним после регистрации
            return redirect("profile")
        except Exception as e:
            error = e.message

    return render(request, "users/register.html", {"error": error})


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def profile_view(request):
    object_usecase = ObjectUseCase()
    system_usecase = SystemUseCase()
    user_objects = object_usecase.list_by_user(request.user)
    user_systems = system_usecase.list_by_user(request.user)
    return render(request, "users/profile.html", {
        "user": request.user,
        "user_objects": user_objects,
        "user_systems": user_systems,
    })
