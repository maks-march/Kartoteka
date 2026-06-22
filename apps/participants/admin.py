from django.contrib import admin

from apps.participants.models import Participant


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ["participant_name"]
    search_fields = ["participant_name"]
