from django.db import models

# Модели юридической принадлежности

class CompanyGroup(models.Model):
    """Группа компаний (холдинг)"""

    name = models.CharField(
        max_length=200,
        verbose_name='Название группы',
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание',
    )

    class Meta:
        verbose_name = 'Группа компаний'
        verbose_name_plural = 'Группы компаний'
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name


class Address(models.Model):
    """Адреса объектов с ФИАС/координатами"""

    country = models.CharField(
        max_length=100,
        verbose_name='Страна',
    )
    region = models.CharField(
        max_length=100,
        verbose_name='Регион',
    )
    city = models.CharField(
        max_length=100,
        verbose_name='Город',
    )
    street = models.CharField(
        max_length=200,
        verbose_name='Улица',
    )
    house = models.CharField(
        max_length=20,
        verbose_name='Дом',
    )
    fias_code = models.CharField(
        max_length=36,
        blank=True,
        null=True,
        verbose_name='Код ФИАС',
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name='Широта',
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name='Долгота',
    )

    class Meta:
        verbose_name = 'Адрес'
        verbose_name_plural = 'Адреса'
        indexes = [
            models.Index(fields=['country', 'city']),
            models.Index(fields=['fias_code']),
        ]

    def __str__(self):
        return f"{self.country}, {self.city}, {self.street}, {self.house}"


class LegalEntity(models.Model):
    """Юридические лица-владельцы"""

    name = models.CharField(
        max_length=200,
        verbose_name='Наименование',
    )
    inn = models.CharField(
        max_length=12,
        unique=True,
        verbose_name='ИНН',
    )
    owner = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name='Собственник',
    )
    group = models.ForeignKey(
        CompanyGroup,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name='Группа компаний',
    )

    class Meta:
        verbose_name = 'Юридическое лицо'
        verbose_name_plural = 'Юридические лица'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['inn']),
            models.Index(fields=['group', 'owner']),
        ]

    def __str__(self):
        return self.name
