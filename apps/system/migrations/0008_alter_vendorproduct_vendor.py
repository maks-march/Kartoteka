# Перевод VendorProduct.vendor с Entity на VendorProfile.
# Шаг 1 (RunPython): для каждого продукта с вендором-Entity создаём
#   (или находим) VendorProfile этого участника и переписываем vendor_id
#   с id участника на id профиля.
# Шаг 2 (AlterField): меняем цель внешнего ключа на entities.VendorProfile.
import django.db.models.deletion
from django.db import migrations, models


def entity_vendor_to_profile(apps, schema_editor):
    VendorProduct = apps.get_model("system", "VendorProduct")
    VendorProfile = apps.get_model("entities", "VendorProfile")

    # На этом шаге vendor_id ещё хранит id УЧАСТНИКА (Entity).
    profile_by_entity = {}
    for product in VendorProduct.objects.exclude(vendor__isnull=True):
        entity_id = product.vendor_id
        profile_id = profile_by_entity.get(entity_id)
        if profile_id is None:
            profile, _ = VendorProfile.objects.get_or_create(entity_id=entity_id)
            profile_id = profile.id
            profile_by_entity[entity_id] = profile_id
        product.vendor_id = profile_id
        product.save(update_fields=["vendor"])


def profile_to_entity_vendor(apps, schema_editor):
    """Обратная миграция: vendor_id профиля -> id участника."""
    VendorProduct = apps.get_model("system", "VendorProduct")
    VendorProfile = apps.get_model("entities", "VendorProfile")
    entity_by_profile = {p.id: p.entity_id for p in VendorProfile.objects.all()}
    for product in VendorProduct.objects.exclude(vendor__isnull=True):
        product.vendor_id = entity_by_profile.get(product.vendor_id)
        product.save(update_fields=["vendor"])


class Migration(migrations.Migration):

    dependencies = [
        ('entities', '0002_engineeringcompanyprofile_functioncompetency_and_more'),
        ('system', '0007_vendorproduct_industries_and_more'),
    ]

    operations = [
        migrations.RunPython(entity_vendor_to_profile, profile_to_entity_vendor),
        migrations.AlterField(
            model_name='vendorproduct',
            name='vendor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='entities.vendorprofile', verbose_name='Вендор'),
        ),
    ]
