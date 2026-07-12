# Бэкфилл: у существующих участников создаём недостающие профили в
# соответствии с типом (в частности, full_cycle_vendor получает все три:
# vendor + supplier + engineering).
from django.db import migrations


def backfill(apps, schema_editor):
    Entity = apps.get_model("entities", "Entity")
    VendorProfile = apps.get_model("entities", "VendorProfile")
    SupplierProfile = apps.get_model("entities", "SupplierProfile")
    EngineeringCompanyProfile = apps.get_model("entities", "EngineeringCompanyProfile")
    SystemIntegratorProfile = apps.get_model("entities", "SystemIntegratorProfile")

    VENDOR = ("vendor", "full_cycle_vendor")
    SUPPLIER = ("supplier", "full_cycle_vendor")
    ENGINEERING = ("engineering_company", "full_cycle_vendor")

    for e in Entity.objects.all():
        t = e.entity_type
        if t in VENDOR:
            VendorProfile.objects.get_or_create(entity=e)
        if t in SUPPLIER:
            SupplierProfile.objects.get_or_create(entity=e)
        if t in ENGINEERING:
            EngineeringCompanyProfile.objects.get_or_create(entity=e)
        if t == "system_integrator":
            SystemIntegratorProfile.objects.get_or_create(entity=e)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("entities", "0004_systemintegratorprofile"),
    ]
    operations = [migrations.RunPython(backfill, noop)]
