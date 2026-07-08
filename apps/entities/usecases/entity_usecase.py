from rest_framework.exceptions import NotFound

from apps.entities.repositories.entity_repository import EntityRepository


class EntityUseCase:
    """Сценарии работы с участниками рынка."""
    def __init__(self, repo=None):
        self.repo = repo or EntityRepository()

    def list(self, search=None, ordering=None):
        return self.repo.get_all(search=search, ordering=ordering)

    def get(self, pk):
        obj = self.repo.get_by_id(pk)
        if not obj:
            raise NotFound("Entity not found")
        return obj

    def _sync_profiles(self, entity):
        """Приводит профили в соответствие с типом участника.

        - vendor / full_cycle_vendor → есть VendorProfile;
        - engineering_company → есть EngineeringCompanyProfile;
        - при смене типа лишний профиль удаляется.
        Профиль вендора НЕ удаляем, если на него ещё ссылаются продукты
        (иначе потеряли бы связь) — вместо этого оставляем.
        """
        from apps.entities.models import VendorProfile, EngineeringCompanyProfile

        # Профиль вендора
        if entity.is_vendor_type:
            VendorProfile.objects.get_or_create(entity=entity)
        else:
            vp = VendorProfile.objects.filter(entity=entity).first()
            if vp and not vp.products.exists():
                vp.delete()

        # Профиль инжиниринговой компании
        if entity.is_engineering_type:
            EngineeringCompanyProfile.objects.get_or_create(entity=entity)
        else:
            EngineeringCompanyProfile.objects.filter(entity=entity).delete()

    def create(self, **data):
        entity = self.repo.create(**data)
        self._sync_profiles(entity)
        return entity

    def update(self, pk, **data):
        obj = self.get(pk)
        entity = self.repo.update(obj, **data)
        self._sync_profiles(entity)
        return entity

    def save_engineering_profile(self, entity, region=None, resident_object_id=None,
                                 product_ids=None, competencies=None):
        """Сохраняет поля профиля инжиниринговой компании.

        competencies — список пар (system_class_id, industry).
        Вызывать только для entity типа engineering_company (профиль уже создан
        в _sync_profiles). Для остальных типов — ничего не делает.
        """
        if not entity.is_engineering_type:
            return None
        from apps.entities.models import (
            EngineeringCompanyProfile, FunctionCompetency,
        )
        from apps.objects.models import Object
        from apps.system.models import VendorProduct, AutomationClass

        profile, _ = EngineeringCompanyProfile.objects.get_or_create(entity=entity)
        profile.region = region or ""
        if resident_object_id in (None, "", "None"):
            profile.resident_object = None
        else:
            profile.resident_object = Object.objects.filter(pk=resident_object_id).first()
        profile.save()

        # Компетенция по продуктам (M2M)
        valid_products = VendorProduct.objects.filter(
            pk__in=[p for p in (product_ids or []) if p not in (None, "", "None")]
        )
        profile.product_competencies.set(valid_products)

        # Компетенция по функции (пары класс+индустрия) — пересобираем целиком
        profile.function_competencies.all().delete()
        for class_id, industry in (competencies or []):
            industry = (industry or "").strip()
            if class_id in (None, "", "None") or not industry:
                continue
            klass = AutomationClass.objects.filter(pk=class_id).first()
            if klass:
                FunctionCompetency.objects.create(
                    profile=profile, system_class=klass, industry=industry
                )
        return profile

    def delete(self, pk):
        obj = self.get(pk)
        return self.repo.delete(obj)
