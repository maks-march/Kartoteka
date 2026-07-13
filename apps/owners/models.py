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
    is_root = models.BooleanField(
        default=True,
        verbose_name="Материнская компания",
        help_text="Выставляется автоматически: True, если у компании нет владельца.",
    )
    inn = models.CharField(
        max_length=12,
        blank=True,
        default="",
        verbose_name="ИНН",
    )

    class Meta:
        verbose_name = "Юридическое лицо"
        verbose_name_plural = "Юридические лица"
        ordering = ["owner_name"]

    def save(self, *args, **kwargs):
        # Материнская компания — та, которой никто не владеет.
        # Флаг всегда синхронизируется с наличием владельца (только авто).
        self.is_root = self.owner_id is None
        super().save(*args, **kwargs)

    def __str__(self):
        return self.owner_name
