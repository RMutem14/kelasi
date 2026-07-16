from django.contrib import admin

from apps.attendance.models import Presence


@admin.register(Presence)
class PresenceAdmin(admin.ModelAdmin):
    list_display = ("eleve", "cours", "classe", "date", "statut", "minutes_retard", "enregistre_par")
    list_filter = ("statut", "date", "classe")
    search_fields = ("eleve__first_name", "eleve__last_name", "justification")
    readonly_fields = ("enregistre_par",)
