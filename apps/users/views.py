"""HTML-представления пользователей: вход, регистрация, профиль."""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from apps.users.usecases.usecase import AuthUseCase
from apps.objects.usecases.object_usecase import ObjectUseCase
from apps.system.usecases.system_usecase import SystemUseCase
from apps.categories.usecases.category_usecase import CategoryUseCase


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Вход пользователя: GET — форма, POST — авторизация и редирект в профиль."""
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
    """Регистрация: GET — форма, POST — создание пользователя и вход."""
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
    """Выход пользователя и редирект на страницу входа."""
    logout(request)
    return redirect("login")


@login_required
def profile_objects(request):
    """Вкладка профиля: объекты, созданные пользователем."""
    search = request.GET.get("search") or None
    usecase = ObjectUseCase()
    objects = usecase.list_by_user(request.user, search=search)
    return render(request, "users/profile_objects.html", {
        "user": request.user,
        "objects": objects,
        "active_tab": "objects",
        "search": search or "",
    })


@login_required
def profile_systems(request):
    """Вкладка профиля: системы, созданные пользователем."""
    search = request.GET.get("search") or None
    usecase = SystemUseCase()
    systems = usecase.list_by_user(request.user, search=search)
    return render(request, "users/profile_systems.html", {
        "user": request.user,
        "systems": systems,
        "active_tab": "systems",
        "search": search or "",
    })


@login_required
def profile_categories(request):
    """Вкладка профиля: категории, созданные пользователем."""
    search = request.GET.get("search") or None
    usecase = CategoryUseCase()
    categories = usecase.list_by_user(request.user, search=search)
    return render(request, "users/profile_categories.html", {
        "user": request.user,
        "categories": categories,
        "active_tab": "categories",
        "search": search or "",
    })
