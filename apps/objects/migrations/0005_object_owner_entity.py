# Manually added for linking objects with legal entities

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("owners", "0001_initial"),
        ("objects", "0004_rename_created_by_object_creator_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="object",
            name="owner_entity",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="owned_objects", to="owners.ownerentity", verbose_name="Юридическое лицо"),
        ),
    ]
