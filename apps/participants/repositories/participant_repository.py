import re

from apps.participants.models import Participant
from common.ordering import apply_ordering


class ParticipantRepository:
    """Доступ к данным участников рынка."""
    ORDERING_FIELDS = {"participant_name"}
    DEFAULT_ORDERING = "participant_name"

    def get_all(self, search=None, ordering=None):
        qs = Participant.objects.all()
        if search:
            # iregex вместо icontains: на SQLite icontains не игнорирует
            # регистр для не-ASCII символов (кириллицы)
            qs = qs.filter(participant_name__iregex=re.escape(search))
        return apply_ordering(qs, ordering, self.ORDERING_FIELDS, self.DEFAULT_ORDERING)

    def get_by_id(self, pk):
        return Participant.objects.filter(pk=pk).first()

    def create(self, **kwargs):
        return Participant.objects.create(**kwargs)

    def update(self, instance, **kwargs):
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    def delete(self, instance):
        instance.delete()
        return instance
