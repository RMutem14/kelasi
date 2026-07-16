from django.test import TestCase

from apps.accounts.enums import UserRole
from apps.accounts.models import User
from apps.core.test_factories import make_user, PASSWORD


class UserModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = make_user(UserRole.ADMIN, first_name="Admin", last_name="Boss")
        cls.enseignant = make_user(UserRole.ENSEIGNANT, first_name="Jean", last_name="Prof")
        cls.directeur = make_user(UserRole.DIRECTEUR_ETUDES, first_name="Marie", last_name="Dir")
        cls.eleve = make_user(UserRole.ELEVE, first_name="Alice", last_name="Eleve")
        cls.parent = make_user(UserRole.PARENT, first_name="Paul", last_name="Parent")

    def test_user_creation(self):
        self.assertEqual(self.admin.role, UserRole.ADMIN)
        self.assertEqual(self.enseignant.role, UserRole.ENSEIGNANT)
        self.assertEqual(self.eleve.role, UserRole.ELEVE)
        self.assertEqual(self.parent.role, UserRole.PARENT)

    def test_role_properties(self):
        self.assertTrue(self.admin.is_admin)
        self.assertFalse(self.admin.is_teacher)

        self.assertTrue(self.enseignant.is_teacher)
        self.assertFalse(self.enseignant.is_admin)

        self.assertTrue(self.directeur.is_director)
        self.assertFalse(self.directeur.is_admin)

        self.assertTrue(self.eleve.is_student)
        self.assertFalse(self.eleve.is_teacher)

        self.assertTrue(self.parent.is_parent)
        self.assertFalse(self.parent.is_student)

    def test_full_name(self):
        self.assertEqual(self.admin.full_name, "Admin Boss")
        self.assertEqual(self.eleve.full_name, "Alice Eleve")

    def test_initials(self):
        self.assertEqual(self.admin.initials, "AB")
        self.assertEqual(self.eleve.initials, "AE")

    def test_short_label(self):
        self.assertIsNotNone(self.admin.short_label)
        self.assertTrue(len(self.admin.short_label) > 0)

    def test_user_authentication(self):
        user = User.objects.get(email=self.eleve.email)
        self.assertTrue(user.check_password(PASSWORD))

    def test_user_str(self):
        self.assertIn("Alice", str(self.eleve))

    def test_email_unique(self):
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email=self.eleve.email,
                password=PASSWORD,
                role=UserRole.ELEVE,
                first_name="Other",
                last_name="User",
            )


class UserRoleEnumTest(TestCase):
    def test_role_values(self):
        self.assertEqual(UserRole.ADMIN.value, "admin")
        self.assertEqual(UserRole.ENSEIGNANT.value, "enseignant")
        self.assertEqual(UserRole.DIRECTEUR_ETUDES.value, "directeur_etudes")
        self.assertEqual(UserRole.ELEVE.value, "eleve")
        self.assertEqual(UserRole.PARENT.value, "parent")

    def test_role_choices(self):
        choices = UserRole.choices
        self.assertEqual(len(choices), 5)
        values = [c[0] for c in choices]
        self.assertIn("admin", values)
        self.assertIn("eleve", values)
