from django.contrib import admin

from apps.schedule.models import Creneau


@admin.register(Creneau)
class CreneauAdmin(admin.ModelAdmin):
    list_display = ("classe", "cours", "enseignant", "jour", "heure_debut", "heure_fin", "salle", "annee_scolaire")
    list_filter = ("jour", "annee_scolaire", "classe")
    search_fields = ("classe__nom", "cours__nom", "enseignant__first_name", "enseignant__last_name", "salle")
