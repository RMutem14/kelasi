from django.contrib import admin

from apps.finance.models import FraisEleve, FraisType, Paiement


class PaiementInline(admin.TabularInline):
    model = Paiement
    extra = 0
    readonly_fields = ("montant", "methode", "reference", "date_paiement", "enregistre_par")


@admin.register(FraisType)
class FraisTypeAdmin(admin.ModelAdmin):
    list_display = ("libelle", "categorie", "montant", "annee_scolaire", "est_obligatoire", "est_recurrent")
    list_filter = ("categorie", "annee_scolaire", "est_obligatoire")
    search_fields = ("libelle",)


@admin.register(FraisEleve)
class FraisEleveAdmin(admin.ModelAdmin):
    list_display = ("eleve", "frais_type", "montant_total", "montant_paye", "montant_restant", "statut", "date_echeance")
    list_filter = ("statut", "annee_scolaire", "frais_type")
    search_fields = ("eleve__first_name", "eleve__last_name")
    inlines = [PaiementInline]
    readonly_fields = ("montant_paye",)


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ("code", "frais_eleve", "montant", "methode", "date_paiement", "enregistre_par")
    list_filter = ("methode", "date_paiement")
    search_fields = ("frais_eleve__eleve__first_name", "frais_eleve__eleve__last_name", "reference")
