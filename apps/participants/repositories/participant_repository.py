import re

from apps.participants.models import Participant


class ParticipantRepository:
    def get_all(self, search=None):
        qs = Participant.objects.all()
        if search:
            # iregex вместо icontains: на SQLite icontains не игнорирует
            # регистр для не-ASCII символов (кириллицы)
            qs = qs.filter(participant_name__iregex=re.escape(search))
        return qs

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
