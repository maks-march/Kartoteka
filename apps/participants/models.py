from django.db import models


class Participant(models.Model):
    participant_name = models.CharField(
        max_length=255,
        verbose_name="Название участника рынка",
    )

    class Meta:
        verbose_name = "Участник рынка"
        verbose_name_plural = "Участники рынка"
        ordering = ["participant_name"]

    def __str__(self):
        return self.participant_name
