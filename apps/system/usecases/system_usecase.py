from apps.system.repositories.system_repository import SystemRepository
from apps.system.repositories.automation_class_repository import AutomationClassRepository
from common.exceptions import NotFoundException, PermissionDeniedError
from rest_framework.exceptions import NotFound
from django.core.exceptions import ValidationError


class SystemUseCase:
    def __init__(self, repo=None, class_repo=None):
        self.repo = repo or SystemRepository()
        self.class_repo = class_repo or AutomationClassRepository()

    def list(self, system_class=None, search=None):
        return self.repo.get_all(system_class=system_class, search=search)

    def list_by_user(self, user, search=None):
        return self.repo.get_by_creator(user, search=search)

    def get(self, pk):
        obj = self.repo.get_by_id(pk)
        if not obj:
            raise NotFound("System not found")
        return obj

    def create(self, user=None, **data):
        class_id = data.get("system_class")
        if class_id is not None and not self.class_repo.get_by_id(class_id):
            raise ValidationError("Automation class not found")
        data['system_class'] = self.class_repo.get_by_id(class_id)
        if user is not None:
            data['creator_id'] = user
        return self.repo.create(**data)

    def update(self, pk, user, **data):
        obj = self.get(pk)
        if obj.creator_id != user:
            raise PermissionDeniedError("Только создатель может редактировать запись")
        class_id = data.get("system_class")
        if class_id is not None and not self.class_repo.get_by_id(class_id):
            raise ValidationError("Automation class not found")
        data['system_class'] = self.class_repo.get_by_id(class_id)
        return self.repo.update(obj, **data)

    def delete(self, pk, user):
        obj = self.get(pk)
        if obj.creator_id != user:
            raise PermissionDeniedError("Только создатель может удалить запись")
        return self.repo.delete(obj)
