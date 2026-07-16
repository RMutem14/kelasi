from django.contrib import admin

from apps.forum.models import Question, Reponse


class ReponseInline(admin.TabularInline):
    model = Reponse
    extra = 0
    readonly_fields = ("auteur", "contenu", "est_validee", "created_at")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("titre", "auteur", "cours", "statut", "nb_reponses", "vue_count", "created_at")
    list_filter = ("statut", "cours", "created_at")
    search_fields = ("titre", "contenu", "auteur__first_name", "auteur__last_name")
    inlines = [ReponseInline]
    readonly_fields = ("vue_count",)


@admin.register(Reponse)
class ReponseAdmin(admin.ModelAdmin):
    list_display = ("question", "auteur", "est_validee", "created_at")
    list_filter = ("est_validee", "created_at")
    search_fields = ("contenu", "auteur__first_name", "auteur__last_name")
