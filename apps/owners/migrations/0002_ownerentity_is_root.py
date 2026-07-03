from django.db import migrations, models


def backfill_is_root(apps, schema_editor):
    """Материнская компания — та, у которой нет владельца (owner is None)."""
    OwnerEntity = apps.get_model("owners", "OwnerEntity")
    OwnerEntity.objects.filter(owner__isnull=True).update(is_root=True)
    OwnerEntity.objects.filter(owner__isnull=False).update(is_root=False)


class Migration(migrations.Migration):

    dependencies = [
        ('owners', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ownerentity',
            name='is_root',
            field=models.BooleanField(default=True, help_text='Выставляется автоматически: True, если у компании нет владельца.', verbose_name='Материнская компания'),
        ),
        migrations.RunPython(backfill_is_root, migrations.RunPython.noop),
    ]
