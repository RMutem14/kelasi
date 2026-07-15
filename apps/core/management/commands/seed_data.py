"""
Commande de gestion pour remplir la base avec des données de démonstration.

Usage :
    python manage.py seed_data
"""
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.enums import UserRole
from apps.accounts.models import User
from apps.academic.models import AnneeScolaire, Classe, Cours, Evaluation
from apps.core.constants import DocumentStatus
from apps.pedagogy.models import DocumentPedagogique
from apps.validation.models import ValidationHistory


class Command(BaseCommand):
    """Remplit la base avec des données de démonstration cohérentes."""

    help = "Crée annees scolaires, classes, cours, documents et evaluations de demo."

    def handle(self, *args, **options):
        self.stdout.write("→ Creation des donnees de demonstration...")

        admin = self._get_or_create_user("admin@elikya.cd", "Admin", "Elikya", UserRole.ADMIN, True, True)
        enseignant1 = self._get_or_create_user("enseignant@elikya.cd", "Jean", "Kabasele", UserRole.ENSEIGNANT)
        enseignant2 = self._get_or_create_user("amani@elikya.cd", "Amani", "Mukendi", UserRole.ENSEIGNANT)
        enseignant3 = self._get_or_create_user("kalala@elikya.cd", "Jean", "Kalala", UserRole.ENSEIGNANT)
        directeur = self._get_or_create_user("directeur@elikya.cd", "Marie", "Tshala", UserRole.DIRECTEUR_ETUDES)
        self._get_or_create_user("eleve@elikya.cd", "Paul", "Mukendi", UserRole.ELEVE)

        annee, created = AnneeScolaire.objects.get_or_create(
            libelle="2026-2027",
            defaults={"date_debut": date(2026, 9, 1), "date_fin": date(2027, 7, 15), "est_active": True},
        )
        self._log_created(created, f"Annee scolaire {annee.libelle}")

        classes_data = [
            ("5eme A", Classe.Niveau.SECONDAIRE, "Section scientifique", enseignant2, 32, Classe.Statut.ACTIVE),
            ("6eme A", Classe.Niveau.SECONDAIRE, "Section pedagogique", enseignant3, 28, Classe.Statut.ACTIVE),
            ("4eme B", Classe.Niveau.SECONDAIRE, "Section litteraire", None, 24, Classe.Statut.A_COMPLETER),
            ("3eme C", Classe.Niveau.SECONDAIRE, "Section scientifique", enseignant1, 30, Classe.Statut.ACTIVE),
            ("2eme D", Classe.Niveau.FINALISTE, "Section scientifique", enseignant2, 22, Classe.Statut.ACTIVE),
            ("1ere E", Classe.Niveau.FINALISTE, "Section litteraire", enseignant3, 18, Classe.Statut.SUSPENDUE),
        ]
        classes = {}
        for nom, niveau, section, titulaire, effectif, statut in classes_data:
            obj, created = Classe.objects.get_or_create(
                nom=nom,
                defaults={"niveau": niveau, "section": section, "titulaire": titulaire,
                          "annee_scolaire": annee, "effectif": effectif, "statut": statut},
            )
            classes[nom] = obj
            self._log_created(created, f"Classe {nom}")

        cours_data = [
            ("Mathematiques", "MATH", classes["5eme A"], enseignant2, 4),
            ("Francais", "FR", classes["5eme A"], enseignant2, 3),
            ("Sciences", "SCI", classes["5eme A"], enseignant2, 2),
            ("Mathematiques", "MATH6", classes["6eme A"], enseignant3, 4),
            ("Francais", "FR6", classes["6eme A"], enseignant3, 3),
            ("Histoire", "HIST", classes["6eme A"], None, 2),
            ("Physique", "PHYS", classes["3eme C"], enseignant1, 3),
            ("Chimie", "CHIM", classes["3eme C"], enseignant1, 2),
            ("Anglais", "ANG", classes["4eme B"], None, 2),
            ("Geographie", "GEO", classes["4eme B"], None, 2),
            ("Informatique", "INFO", classes["2eme D"], enseignant2, 3),
            ("Philosophie", "PHILO", classes["1ere E"], enseignant3, 2),
        ]
        cours_map = {}
        for nom, code, classe, enseignant, coef in cours_data:
            obj, created = Cours.objects.get_or_create(
                code=code,
                defaults={"nom": nom, "classe": classe, "enseignant": enseignant,
                          "coefficient": coef,
                          "statut": Cours.Statut.ACTIF if enseignant else Cours.Statut.SANS_ENSEIGNANT},
            )
            cours_map[code] = obj
            self._log_created(created, f"Cours {nom} ({code})")

        docs_data = [
            ("Preparation Algebre", DocumentPedagogique.Type.FICHE_PREPARATION,
             enseignant2, classes["5eme A"], cours_map["MATH"], DocumentStatus.SOUMIS,
             "Preparation sur les equations du 2nd degre."),
            ("Journal du 2e trimestre", DocumentPedagogique.Type.JOURNAL_CLASSE,
             enseignant3, classes["6eme A"], cours_map["FR6"], DocumentStatus.CORRECTION,
             "Journal de classe a completer."),
            ("Cahier des cotes T1", DocumentPedagogique.Type.CAHIER_COTES,
             enseignant2, classes["5eme A"], cours_map["MATH"], DocumentStatus.VALIDE,
             "Cotes du 1er trimestre validees."),
            ("Composition Math T2", DocumentPedagogique.Type.CAHIER_COMPOSITION,
             enseignant1, classes["3eme C"], cours_map["PHYS"], DocumentStatus.BROUILLON,
             "Composition de physique en cours."),
            ("Fiche prevision Sciences", DocumentPedagogique.Type.FICHE_PREVISION,
             enseignant2, classes["5eme A"], cours_map["SCI"], DocumentStatus.VALIDE,
             "Prevision annuelle des sciences."),
            ("Journal classe 3eme C", DocumentPedagogique.Type.JOURNAL_CLASSE,
             enseignant1, classes["3eme C"], cours_map["PHYS"], DocumentStatus.SOUMIS,
             "Journal de physique a valider."),
            ("Cahier cotes Francais 6A", DocumentPedagogique.Type.CAHIER_COTES,
             enseignant3, classes["6eme A"], cours_map["FR6"], DocumentStatus.VALIDE,
             "Cotes de francais validees."),
            ("Preparation Geometrie", DocumentPedagogique.Type.FICHE_PREPARATION,
             enseignant2, classes["2eme D"], cours_map["INFO"], DocumentStatus.BROUILLON,
             "Preparation en cours de redaction."),
            ("Composition Informatique", DocumentPedagogique.Type.CAHIER_COMPOSITION,
             enseignant2, classes["2eme D"], cours_map["INFO"], DocumentStatus.REJETE,
             "Composition rejetée — a refaire."),
            ("Prevision Philosophie", DocumentPedagogique.Type.FICHE_PREVISION,
             enseignant3, classes["1ere E"], cours_map["PHILO"], DocumentStatus.SOUMIS,
             "Prevision philosophie a valider."),
            ("Journal Chimie 3C", DocumentPedagogique.Type.JOURNAL_CLASSE,
             enseignant1, classes["3eme C"], cours_map["CHIM"], DocumentStatus.VALIDE,
             "Journal de chimie valide."),
            ("Cahier cotes Histoire 6A", DocumentPedagogique.Type.CAHIER_COTES,
             enseignant3, classes["6eme A"], cours_map["HIST"], DocumentStatus.CORRECTION,
             "Cotes a corriger."),
            ("Preparation Anglais 4B", DocumentPedagogique.Type.FICHE_PREPARATION,
             enseignant3, classes["4eme B"], cours_map["ANG"], DocumentStatus.BROUILLON,
             "Preparation en brouillon."),
            ("Fiche prevision Geographie", DocumentPedagogique.Type.FICHE_PREVISION,
             enseignant3, classes["4eme B"], cours_map["GEO"], DocumentStatus.SOUMIS,
             "Prevision geographie soumise."),
            ("Composition Math 6A", DocumentPedagogique.Type.CAHIER_COMPOSITION,
             enseignant3, classes["6eme A"], cours_map["MATH6"], DocumentStatus.VALIDE,
             "Composition validee."),
            ("Journal Physique 2D", DocumentPedagogique.Type.JOURNAL_CLASSE,
             enseignant2, classes["2eme D"], cours_map["INFO"], DocumentStatus.SOUMIS,
             "Journal informatique a valider."),
            ("Cahier cotes Philosophie", DocumentPedagogique.Type.CAHIER_COTES,
             enseignant3, classes["1ere E"], cours_map["PHILO"], DocumentStatus.BROUILLON,
             "Brouillon — pas encore soumis."),
            ("Preparation Sciences 5A", DocumentPedagogique.Type.FICHE_PREPARATION,
             enseignant2, classes["5eme A"], cours_map["SCI"], DocumentStatus.VALIDE,
             "Preparation validee."),
        ]
        for titre, type_doc, auteur, classe, cours, statut, desc in docs_data:
            obj, created = DocumentPedagogique.objects.get_or_create(
                titre=titre,
                defaults={"type": type_doc, "auteur": auteur, "classe": classe, "cours": cours,
                          "statut": statut, "description": desc,
                          "date_soumission": timezone.now() if statut != DocumentStatus.BROUILLON else None,
                          "date_validation": timezone.now() if statut == DocumentStatus.VALIDE else None},
            )
            self._log_created(created, f"Document {titre[:40]}")

        evals_data = [
            ("Controle 1 - Algebre", Evaluation.Type.INTERROGATION, enseignant2,
             classes["5eme A"], cours_map["MATH"], date.today() + timedelta(days=7), 60, 20, Evaluation.Statut.PROGRAMMEE),
            ("Devoir 1 - Francais", Evaluation.Type.DEVOIR, enseignant3,
             classes["6eme A"], cours_map["FR6"], date.today() - timedelta(days=3), 120, 20, Evaluation.Statut.TERMINEE),
            ("Examen Physique", Evaluation.Type.EXAMEN, enseignant1,
             classes["3eme C"], cours_map["PHYS"], date.today() + timedelta(days=14), 180, 40, Evaluation.Statut.PROGRAMMEE),
            ("TP Informatique", Evaluation.Type.TP, enseignant2,
             classes["2eme D"], cours_map["INFO"], date.today() - timedelta(days=1), 90, 15, Evaluation.Statut.CORRIGEE),
            ("Interrogation Chimie", Evaluation.Type.INTERROGATION, enseignant1,
             classes["3eme C"], cours_map["CHIM"], date.today() + timedelta(days=2), 30, 10, Evaluation.Statut.PROGRAMMEE),
            ("Devoir Philosophie", Evaluation.Type.DEVOIR, enseignant3,
             classes["1ere E"], cours_map["PHILO"], date.today() - timedelta(days=7), 120, 20, Evaluation.Statut.TERMINEE),
        ]
        for titre, type_eval, enseignant, classe, cours, date_eval, duree, sur, statut in evals_data:
            obj, created = Evaluation.objects.get_or_create(
                titre=titre,
                defaults={"type": type_eval, "enseignant": enseignant, "classe": classe, "cours": cours,
                          "date_evaluation": date_eval, "duree_minutes": duree, "sur": sur, "statut": statut},
            )
            self._log_created(created, f"Evaluation {titre[:40]}")

        docs_valides = DocumentPedagogique.objects.filter(statut=DocumentStatus.VALIDE)
        for doc in docs_valides[:3]:
            ValidationHistory.objects.get_or_create(
                document=doc, action=DocumentStatus.VALIDE,
                defaults={"action_par": directeur, "commentaire": "Document valide apres revue."},
            )

        # ------------------------------------------------------------
        # 8. Ressources marketplace
        # ------------------------------------------------------------
        from apps.marketplace.models import Resource as MarketResource
        from apps.core.constants import PublicationStatus, ResourceType, ResourceCategory
        from django.core.files.base import ContentFile

        ressources_data = [
            ("Syllabus complet d Algebre", "Cours complet sur l algebre lineaire pour la 5eme secondaire.",
             enseignant2, classes.get("5eme A"), cours_map.get("MATH"),
             ResourceType.SYLLABUS, ResourceCategory.COURS, 15, PublicationStatus.PUBLIE),
            ("Recueil d exercices de Francais", "200 exercices de grammaire et conjugaison.",
             enseignant3, classes.get("6eme A"), cours_map.get("FR6"),
             ResourceType.EXERCICE, ResourceCategory.EXERCICE, 5, PublicationStatus.PUBLIE),
            ("Examen type - Physique", "Examen complet avec corrige detaille.",
             enseignant1, classes.get("3eme C"), cours_map.get("PHYS"),
             ResourceType.EXAMEN, ResourceCategory.EVALUATION, 8, PublicationStatus.PUBLIE),
            ("Support de cours - Informatique", "Introduction a la programmation Python.",
             enseignant2, classes.get("2eme D"), cours_map.get("INFO"),
             ResourceType.SUPPORT, ResourceCategory.COURS, 0, PublicationStatus.PUBLIE),
            ("Livre numerique - Chimie", "Manuel complet de chimie organique.",
             enseignant1, classes.get("3eme C"), cours_map.get("CHIM"),
             ResourceType.LIVRE, ResourceCategory.REFERENCE, 20, PublicationStatus.PUBLIE),
            ("Corriges - Mathematiques 6A", "Corriges de tous les exercices du trimestre.",
             enseignant3, classes.get("6eme A"), cours_map.get("MATH6"),
             ResourceType.CORRIGE, ResourceCategory.EXERCICE, 3, PublicationStatus.BROUILLON),
        ]
        for titre, desc, auteur, classe, cours, type_r, cat, prix, statut in ressources_data:
            obj, created = MarketResource.objects.get_or_create(
                titre=titre,
                defaults={"description": desc, "auteur": auteur, "classe": classe, "cours": cours,
                          "type": type_r, "categorie": cat, "prix": prix, "statut": statut},
            )
            if created and not obj.fichier:
                fake_content = ContentFile(b"%PDF-1.4\nFake PDF content for " + titre.encode())
                obj.fichier.save(f"{titre[:30]}.pdf", fake_content)
            self._log_created(created, f"Ressource {titre[:40]}")

        # ------------------------------------------------------------
        # 9. Notes de l eleve
        # ------------------------------------------------------------
        from apps.students.models import Note
        eleve_obj = User.objects.filter(email="eleve@elikya.cd").first()
        if eleve_obj:
            evals = Evaluation.objects.all()
            notes_data = [
                (evals[0], 16, "Tres bon travail"),
                (evals[1], 12, "Peut mieux faire"),
                (evals[3], 18, "Excellent"),
                (evals[4], 8, "Insuffisant, revoir le cours"),
            ]
            for eval_obj, valeur, appr in notes_data:
                if eval_obj:
                    obj, created = Note.objects.get_or_create(
                        eleve=eleve_obj, evaluation=eval_obj,
                        defaults={"valeur": valeur, "appreciation": appr},
                    )
                    self._log_created(created, f"Note {valeur}/{eval_obj.sur} pour {eval_obj.titre[:30]}")

        # ------------------------------------------------------------
        # 10. Notifications
        # ------------------------------------------------------------
        from apps.notifications.models import Notification
        from apps.core.constants import NotificationLevel

        notifs_data = [
            (admin, "Bienvenue sur Huduma", "Votre plateforme pedagogique est prete.",
             NotificationLevel.INFO, "/dashboard/"),
            (enseignant2, "Nouvelle vente", "Un eleve a achete votre ressource.",
             NotificationLevel.SUCCESS, "/marketplace/mes-ventes/"),
            (enseignant2, "Document valide", "Votre document a ete valide.",
             NotificationLevel.SUCCESS, "/pedagogy/"),
            (directeur, "Nouveau document a valider", "Un nouveau document a ete soumis.",
             NotificationLevel.WARNING, "/validation/documents/"),
            (eleve_obj or admin, "Notes disponibles", "Vos notes sont disponibles.",
             NotificationLevel.INFO, "/students/notes/"),
            (admin, "Mise a jour systeme", "Maintenance prevue ce week-end.",
             NotificationLevel.WARNING, ""),
        ]
        for dest, titre, msg, niveau, url in notifs_data:
            obj, created = Notification.objects.get_or_create(
                destinataire=dest, titre=titre,
                defaults={"message": msg, "niveau": niveau, "url": url},
            )
            self._log_created(created, f"Notification '{titre[:30]}' pour {dest.email}")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("Donnees de demonstration creees :"))
        self.stdout.write(f"  - {AnneeScolaire.objects.count()} annee(s) scolaire(s)")
        self.stdout.write(f"  - {Classe.objects.count()} classe(s)")
        self.stdout.write(f"  - {Cours.objects.count()} cours")
        self.stdout.write(f"  - {DocumentPedagogique.objects.count()} document(s) pedagogique(s)")
        self.stdout.write(f"  - {Evaluation.objects.count()} evaluation(s)")
        self.stdout.write(f"  - {ValidationHistory.objects.count()} historique(s) de validation")
        self.stdout.write(f"  - {MarketResource.objects.count()} ressource(s) marketplace")
        self.stdout.write(f"  - {Note.objects.count()} note(s)")
        self.stdout.write(f"  - {Notification.objects.count()} notification(s)")
        self.stdout.write(f"  - {User.objects.count()} utilisateur(s)")
        self.stdout.write(self.style.SUCCESS("=" * 50))

    def _get_or_create_user(self, email, first_name, last_name, role, is_staff=False, is_superuser=False):
        user, created = User.objects.get_or_create(
            email=email,
            defaults={"first_name": first_name, "last_name": last_name, "role": role,
                      "is_staff": is_staff, "is_superuser": is_superuser, "is_active": True},
        )
        if created:
            user.set_password("Huduma2026!")
            user.save()
        return user

    def _log_created(self, created, label):
        if created:
            self.stdout.write(self.style.SUCCESS(f"  +  Cree : {label}"))
        else:
            self.stdout.write(f"  -  Existe : {label}")
