from django.db import models


class OwnerEntity(models.Model):
    owner_name = models.CharField(
        max_length=255,
        verbose_name="Название юр. лица",
    )
    owner = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subsidiaries",
        verbose_name="Следующий в иерархии владелец",
    )
    ultimate_owner = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ultimate_owned_entities",
        verbose_name="Корневой владелец",
    )

    class Meta:
        verbose_name = "Юридическое лицо"
        verbose_name_plural = "Юридические лица"
        ordering = ["owner_name"]

    def __str__(self):
        return self.owner_name
