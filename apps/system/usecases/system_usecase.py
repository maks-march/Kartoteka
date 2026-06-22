from apps.system.repositories.system_repository import SystemRepository
from apps.system.repositories.automation_class_repository import AutomationClassRepository
from apps.participants.repositories.participant_repository import ParticipantRepository
from common.exceptions import NotFoundException
from rest_framework.exceptions import NotFound
from django.core.exceptions import ValidationError


class SystemUseCase:
    def __init__(self, repo=None, class_repo=None, participant_repo=None):
        self.repo = repo or SystemRepository()
        self.class_repo = class_repo or AutomationClassRepository()
        self.participant_repo = participant_repo or ParticipantRepository()

    def list(self, system_class=None, search=None, obj=None):
        return self.repo.get_all(system_class=system_class, search=search, obj=obj)

    def list_by_user(self, user, search=None):
        return self.repo.get_by_creator(user, search=search)

    def get(self, pk):
        obj = self.repo.get_by_id(pk)
        if not obj:
            raise NotFound("System not found")
        return obj

    def _get_optional_participant(self, pk, field_name):
        if pk in (None, "", "None"):
            return None
        participant = self.participant_repo.get_by_id(pk)
        if not participant:
            raise ValidationError(f"{field_name} не найден")
        return participant

    def create(self, user=None, **data):
        class_id = data.get("system_class")
        if class_id is not None and not self.class_repo.get_by_id(class_id):
            raise ValidationError("Automation class not found")
        data['system_class'] = self.class_repo.get_by_id(class_id)

        vendor_id = data.pop("vendor", None)
        data["vendor"] = self._get_optional_participant(vendor_id, "Вендор")

        if user is not None:
            data['creator_id'] = user
        return self.repo.create(**data)

    def update(self, pk, user, **data):
        obj = self.get(pk)
        class_id = data.get("system_class")
        if class_id is not None and not self.class_repo.get_by_id(class_id):
            raise ValidationError("Automation class not found")
        data['system_class'] = self.class_repo.get_by_id(class_id)

        if "vendor" in data:
            vendor_id = data.pop("vendor")
            data["vendor"] = self._get_optional_participant(vendor_id, "Вендор")

        return self.repo.update(obj, **data)

    def delete(self, pk, user):
        obj = self.get(pk)
        return self.repo.delete(obj)
