# core/decorators.py
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages


def group_required(*group_names):
    """Декоратор для проверки membership в группах"""

    def in_groups(user):
        if user.is_authenticated:
            if user.is_superuser or user.groups.filter(name__in=group_names).exists():
                return True
        return False

    return user_passes_test(in_groups, login_url='login', redirect_field_name=None)


def editor_required(view_func):
    """Декоратор для редакторов (могут редактировать)"""

    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        if request.user.is_superuser or request.user.groups.filter(name='Редакторы').exists():
            return view_func(request, *args, **kwargs)

        messages.error(request, 'У вас нет прав для этого действия')
        return redirect('overview')

    return wrapper


def viewer_required(view_func):
    """Декоратор для просмотрщиков (только просмотр)"""

    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        if request.user.is_superuser or request.user.groups.filter(
                name__in=['Редакторы', 'Просмотрщики']
        ).exists():
            return view_func(request, *args, **kwargs)

        messages.error(request, 'У вас нет прав для просмотра')
        return redirect('overview')

    return wrapper


def can_edit_object(obj, user):
    """Проверка может ли пользователь редактировать конкретный объект"""
    if user.is_superuser:
        return True
    if user.groups.filter(name='Редакторы').exists():
        return True
    return hasattr(obj, 'created_by') and obj.created_by == user


def can_delete_object(obj, user):
    """Проверка может ли пользователь удалить объект"""
    return user.is_superuser
