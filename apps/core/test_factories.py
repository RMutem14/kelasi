"""
Factory de base pour les tests Huduma.

Crée les objets communs (année scolaire, classe, cours, utilisateurs) réutilisables.
"""
from datetime import date

from django.contrib.auth import get_user_model

from apps.accounts.enums import UserRole
from apps.academic.models import AnneeScolaire, Classe, Cours, Evaluation
from apps.students.models import Periode

User = get_user_model()

PASSWORD = "Huduma2026!"


def make_user(role, first_name="Test", last_name="User", email=None, **kwargs):
    """Crée un utilisateur avec un rôle donné."""
    if email is None:
        email = f"{role}.{first_name}.{last_name}@test.huduma".lower()
    return User.objects.create_user(
        email=email,
        password=PASSWORD,
        role=role,
        first_name=first_name,
        last_name=last_name,
        **kwargs,
    )


def make_annee(libelle="2026-2027", active=True):
    annee, _created = AnneeScolaire.objects.get_or_create(
        libelle=libelle,
        defaults={
            "date_debut": date(2026, 9, 1),
            "date_fin": date(2027, 7, 31),
            "est_active": active,
        },
    )
    return annee


def make_classe(nom="5ème A", annee=None):
    if annee is None:
        annee = make_annee()
    return Classe.objects.create(
        nom=nom,
        niveau=Classe.Niveau.SECONDAIRE,
        annee_scolaire=annee,
        statut=Classe.Statut.ACTIVE,
    )


def make_cours(classe=None, nom="Mathématiques", code=None, coef=2, enseignant=None):
    if classe is None:
        classe = make_classe()
    if code is None:
        import uuid
        code = f"C{uuid.uuid4().hex[:6].upper()}"
    return Cours.objects.create(
        nom=nom,
        code=code,
        classe=classe,
        coefficient=coef,
        enseignant=enseignant,
        statut=Cours.Statut.ACTIF,
    )


def make_evaluation(cours=None, classe=None, enseignant=None, titre="Devoir 1", sur=20):
    if cours is None:
        cours = make_cours()
    if classe is None:
        classe = cours.classe
    if enseignant is None:
        enseignant = make_user(UserRole.ENSEIGNANT, first_name="Prof", last_name="Test")
    return Evaluation.objects.create(
        titre=titre,
        type=Evaluation.Type.DEVOIR,
        enseignant=enseignant,
        classe=classe,
        cours=cours,
        date_evaluation=date(2026, 10, 15),
        sur=sur,
        statut=Evaluation.Statut.CORRIGEE,
    )


def make_periode(annee=None, libelle="1er terme", ordre=1):
    if annee is None:
        annee = make_annee()
    return Periode.objects.create(
        libelle=libelle,
        ordre=ordre,
        annee_scolaire=annee,
        date_debut=date(2026, 9, 1),
        date_fin=date(2026, 12, 31),
        est_active=True,
    )
