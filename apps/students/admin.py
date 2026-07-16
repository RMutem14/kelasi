from django.contrib import admin

from apps.students.models import Bulletin, BulletinLine, Note, Periode, ResourceAccess


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("eleve", "evaluation", "valeur", "date_saisie")
    list_filter = ("evaluation__classe",)
    search_fields = ("eleve__first_name", "eleve__last_name")


@admin.register(ResourceAccess)
class ResourceAccessAdmin(admin.ModelAdmin):
    list_display = ("eleve", "ressource", "created_at")
    search_fields = ("eleve__first_name", "eleve__last_name")


@admin.register(Periode)
class PeriodeAdmin(admin.ModelAdmin):
    list_display = ("libelle", "ordre", "annee_scolaire", "date_debut", "date_fin", "est_active")
    list_filter = ("annee_scolaire", "est_active")
    search_fields = ("libelle",)


class BulletinLineInline(admin.TabularInline):
    model = BulletinLine
    extra = 0
    readonly_fields = ("cours", "coefficient", "moyenne_cours", "points", "mention_cours")


@admin.register(Bulletin)
class BulletinAdmin(admin.ModelAdmin):
    list_display = ("eleve", "classe", "periode", "moyenne_generale", "rang", "statut", "date_publication")
    list_filter = ("statut", "classe", "periode")
    search_fields = ("eleve__first_name", "eleve__last_name")
    inlines = [BulletinLineInline]
    readonly_fields = ("moyenne_generale", "total_points", "total_coefficients", "rang", "effectif_classe", "date_publication")
