"""
Commande de gestion pour créer des utilisateurs de test.

Usage :
    python manage.py seed_users

Crée un superuser admin + un utilisateur par rôle (enseignant,
directeur, eleve) pour faciliter les tests et la démonstration.
"""
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from apps.accounts.enums import UserRole
from apps.accounts.models import User


class Command(BaseCommand):
    """Crée des utilisateurs de test pour le Sprint 0."""

    help = "Crée un superuser admin + un utilisateur par rôle pour les tests."

    def handle(self, *args, **options):
        users_to_create = [
            {
                "email": "admin@elikya.cd",
                "password": "Huduma2026!",
                "first_name": "Admin",
                "last_name": "Elikya",
                "role": UserRole.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
            {
                "email": "enseignant@elikya.cd",
                "password": "Huduma2026!",
                "first_name": "Jean",
                "last_name": "Kabasele",
                "role": UserRole.ENSEIGNANT,
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "email": "directeur@elikya.cd",
                "password": "Huduma2026!",
                "first_name": "Marie",
                "last_name": "Tshala",
                "role": UserRole.DIRECTEUR_ETUDES,
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "email": "eleve@elikya.cd",
                "password": "Huduma2026!",
                "first_name": "Paul",
                "last_name": "Mukendi",
                "role": UserRole.ELEVE,
                "is_staff": False,
                "is_superuser": False,
            },
        ]

        created_count = 0
        skipped_count = 0

        for user_data in users_to_create:
            email = user_data.pop("email")
            password = user_data.pop("password")
            try:
                if User.objects.filter(email=email).exists():
                    self.stdout.write(
                        self.style.WARNING(f"  ⚠  {email} existe deja -- ignore.")
                    )
                    skipped_count += 1
                    continue

                user = User.objects.create_user(
                    email=email,
                    password=password,
                    **user_data,
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  +  Cree : {user.full_name} <{email}> ({user.role})"
                    )
                )
                created_count += 1
            except IntegrityError as exc:
                self.stdout.write(
                    self.style.ERROR(f"  x  Erreur pour {email} : {exc}")
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Termine : {created_count} cree(s), {skipped_count} ignore(s)."
            )
        )
        self.stdout.write("")
        self.stdout.write("Comptes de test (mot de passe : Huduma2026!) :")
        self.stdout.write("  - admin@elikya.cd       (Administrateur + superuser)")
        self.stdout.write("  - enseignant@elikya.cd  (Enseignant)")
        self.stdout.write("  - directeur@elikya.cd   (Directeur des etudes)")
        self.stdout.write("  - eleve@elikya.cd       (Eleve)")
