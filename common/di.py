"""Wire — ручной DI-контейнер."""

from apps.users import DjangoUserRepository
from apps.users import RegisterUserUseCase
from apps.users import AuthenticateUserUseCase

from objects_app.repository.category_impl import DjangoCategoryRepository
from objects_app.repository.object_impl import DjangoObjectRepository
from objects_app.usecase.create_category import CreateCategoryUseCase
from objects_app.usecase.update_category import UpdateCategoryUseCase
from objects_app.usecase.delete_category import DeleteCategoryUseCase
from objects_app.usecase.get_category import GetCategoryByIdUseCase, ListCategoriesUseCase, GetCategoryObjectCountUseCase
from objects_app.usecase.create_object import CreateObjectUseCase
from objects_app.usecase.update_object import UpdateObjectUseCase
from objects_app.usecase.delete_object import DeleteObjectUseCase
from objects_app.usecase.get_object import GetObjectByIdUseCase, ListObjectsUseCase


def make_user_repo():
    return DjangoUserRepository()


def make_register_usecase():
    return RegisterUserUseCase(user_repo=make_user_repo())


def make_authenticate_usecase():
    return AuthenticateUserUseCase(user_repo=make_user_repo())


def make_category_repo():
    return DjangoCategoryRepository()


def make_object_repo():
    return DjangoObjectRepository()


def make_create_category_usecase():
    return CreateCategoryUseCase(category_repo=make_category_repo())


def make_update_category_usecase():
    return UpdateCategoryUseCase(category_repo=make_category_repo())


def make_delete_category_usecase():
    return DeleteCategoryUseCase(category_repo=make_category_repo())


def make_get_category_by_id_usecase():
    return GetCategoryByIdUseCase(category_repo=make_category_repo())


def make_list_categories_usecase():
    return ListCategoriesUseCase(category_repo=make_category_repo())


def make_get_category_object_count_usecase():
    return GetCategoryObjectCountUseCase(category_repo=make_category_repo())


def make_create_object_usecase():
    return CreateObjectUseCase(object_repo=make_object_repo(), category_repo=make_category_repo())


def make_update_object_usecase():
    return UpdateObjectUseCase(object_repo=make_object_repo(), category_repo=make_category_repo())


def make_delete_object_usecase():
    return DeleteObjectUseCase(object_repo=make_object_repo())


def make_get_object_by_id_usecase():
    return GetObjectByIdUseCase(object_repo=make_object_repo())


def make_list_objects_usecase():
    return ListObjectsUseCase(object_repo=make_object_repo())
