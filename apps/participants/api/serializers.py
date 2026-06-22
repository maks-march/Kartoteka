from rest_framework import serializers

from apps.participants.models import Participant


class ParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participant
        fields = ["id", "participant_name"]


class ParticipantCreateUpdateSerializer(serializers.Serializer):
    participant_name = serializers.CharField(max_length=255)
