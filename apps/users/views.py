from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from apps.users.usecases.usecase import AuthUseCase


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
            error = str(e)

    return render(request, "auth_service/login.html", {"error": error})


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
            error = str(e)

    return render(request, "auth_service/register.html", {"error": error})


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def profile_view(request):
    return render(request, "auth_service/profile.html", {"user": request.user})
