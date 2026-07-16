"""
Services pour la génération et la gestion des bulletins de notes.
"""
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.academic.models import Cours
from apps.students.models import Bulletin, BulletinLine, Note


class BulletinGenerator:
    """Génère ou régénère un bulletin pour un élève et une période."""

    def __init__(self, eleve, classe, periode):
        self.eleve = eleve
        self.classe = classe
        self.periode = periode

    @transaction.atomic
    def generate(self, publie_par=None, statut=Bulletin.Statut.BROUILLON):
        """Crée ou met à jour le bulletin avec ses lignes."""
        bulletin, _created = Bulletin.objects.update_or_create(
            eleve=self.eleve,
            periode=self.periode,
            defaults={
                "classe": self.classe,
                "annee_scolaire": self.periode.annee_scolaire,
                "statut": statut,
                "publie_par": publie_par,
            },
        )

        # Supprime les anciennes lignes pour les régénérer
        bulletin.lignes.all().delete()

        # Récupère tous les cours de la classe
        cours_list = Cours.objects.filter(classe=self.classe).order_by("nom")

        ordre = 1
        for cours in cours_list:
            moyenne = self._calculer_moyenne_cours(cours)
            if moyenne is None:
                continue

            appreciation = self._generer_appreciation(moyenne)

            BulletinLine.objects.create(
                bulletin=bulletin,
                cours=cours,
                coefficient=cours.coefficient,
                moyenne_cours=moyenne,
                appreciation=appreciation,
                ordre=ordre,
            )
            ordre += 1

        # Calcule la moyenne générale
        bulletin.calculer_moyenne()
        bulletin.calculer_rang()
        bulletin.save()

        return bulletin

    def _calculer_moyenne_cours(self, cours):
        """Calcule la moyenne d'un cours sur 20 pour la période.

        Récupère toutes les notes de l'élève pour les évaluations
        de ce cours comprises dans la période.
        """
        notes = Note.objects.filter(
            eleve=self.eleve,
            evaluation__cours=cours,
            evaluation__date_evaluation__gte=self.periode.date_debut,
            evaluation__date_evaluation__lte=self.periode.date_fin,
        ).select_related("evaluation")

        if not notes.exists():
            return None

        total_pondere = Decimal("0")
        total_max = Decimal("0")

        for note in notes:
            # Normalise la note sur 20
            sur = Decimal(str(note.evaluation.sur))
            if sur <= 0:
                continue
            note_sur_20 = (Decimal(str(note.valeur)) / sur) * Decimal("20")
            total_pondere += note_sur_20
            total_max += Decimal("20")

        if total_max == 0:
            return None

        return (total_pondere / total_max).quantize(Decimal("0.01"))

    @staticmethod
    def _generer_appreciation(moyenne):
        """Génère une appréciation automatique selon la moyenne."""
        moy = float(moyenne)
        if moy >= 16:
            return "Très bon résultat. Continuez ainsi."
        elif moy >= 14:
            return "Bon travail. Peut mieux faire."
        elif moy >= 12:
            return "Travail assez satisfaisant. Efforts à maintenir."
        elif moy >= 10:
            return "Résultat passable. Plus d'efforts nécessaires."
        elif moy >= 8:
            return "Travail insuffisant. Doit se ressaisir."
        else:
            return "Résultat très insuffisant. Travail sérieux requis."


class ClasseBulletinGenerator:
    """Génère les bulletins pour tous les élèves d'une classe."""

    @transaction.atomic
    def generate_all(self, classe, periode, publie_par=None, statut=Bulletin.Statut.BROUILLON):
        """Génère les bulletins pour tous les élèves d'une classe.

        Returns:
            tuple: (nb_generes, nb_vides) — bulletins générés et bulletins sans notes.
        """
        from apps.accounts.enums import UserRole
        from apps.accounts.models import User

        eleves = User.objects.filter(
            role=UserRole.ELEVE,
            is_active=True,
        ).filter(
            notes__evaluation__classe=classe,
            notes__evaluation__date_evaluation__gte=periode.date_debut,
            notes__evaluation__date_evaluation__lte=periode.date_fin,
        ).distinct()

        nb_generes = 0
        nb_vides = 0

        for eleve in eleves:
            gen = BulletinGenerator(eleve, classe, periode)
            bulletin = gen.generate(publie_par=publie_par, statut=statut)
            if bulletin.lignes.exists():
                nb_generes += 1
            else:
                nb_vides += 1

        # Recalcule les rangs pour tous les bulletins de la classe
        bulletins = Bulletin.objects.filter(classe=classe, periode=periode)
        for bull in bulletins:
            bull.calculer_rang()
            bull.save()

        return nb_generes, nb_vides


def publish_bulletin(bulletin, user):
    """Publie un bulletin (passe du statut brouillon à publié)."""
    bulletin.statut = Bulletin.Statut.PUBLIE
    bulletin.date_publication = timezone.now()
    bulletin.publie_par = user
    bulletin.save()
    return bulletin


def publish_all_bulletins(classe, periode, user):
    """Publie tous les bulletins brouillons d'une classe pour une période."""
    bulletins = Bulletin.objects.filter(
        classe=classe,
        periode=periode,
        statut=Bulletin.Statut.BROUILLON,
    )
    now = timezone.now()
    for bull in bulletins:
        bull.statut = Bulletin.Statut.PUBLIE
        bull.date_publication = now
        bull.publie_par = user
        bull.save()
    return bulletins.count()
