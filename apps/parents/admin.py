from django.contrib import admin

from apps.parents.models import ParentEleve


@admin.register(ParentEleve)
class ParentEleveAdmin(admin.ModelAdmin):
    list_display = ("parent", "eleve", "relation", "est_contact_principal", "autorise_consultation")
    list_filter = ("relation", "est_contact_principal", "autorise_consultation")
    search_fields = ("parent__first_name", "parent__last_name", "eleve__first_name", "eleve__last_name")
