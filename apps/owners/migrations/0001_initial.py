# Manually added for OwnerEntity

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name="OwnerEntity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("owner_name", models.CharField(max_length=255, verbose_name="Название юр. лица")),
                ("owner", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="subsidiaries", to="owners.ownerentity", verbose_name="Следующий в иерархии владелец")),
                ("ultimate_owner", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="ultimate_owned_entities", to="owners.ownerentity", verbose_name="Корневой владелец")),
            ],
            options={
                "verbose_name": "Юридическое лицо",
                "verbose_name_plural": "Юридические лица",
                "ordering": ["owner_name"],
            },
        ),
    ]
