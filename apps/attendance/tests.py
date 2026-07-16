from datetime import date

from django.test import TestCase
from django.urls import reverse

from apps.accounts.enums import UserRole
from apps.attendance.models import Presence
from apps.core.test_factories import (
    make_classe, make_cours, make_user, PASSWORD,
)


class PresenceModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.enseignant = make_user(UserRole.ENSEIGNANT, first_name="Prof", last_name="Att")
        cls.eleve = make_user(UserRole.ELEVE, first_name="Carl", last_name="Elv")
        cls.classe = make_classe()
        cls.cours = make_cours(classe=cls.classe, enseignant=cls.enseignant)
        cls.presence = Presence.objects.create(
            eleve=cls.eleve,
            cours=cls.cours,
            classe=cls.classe,
            date=date(2026, 10, 15),
            statut=Presence.Statut.PRESENT,
            enregistre_par=cls.enseignant,
            created_by=cls.enseignant,
        )

    def test_str(self):
        self.assertIn("Carl", str(self.presence))

    def test_est_absent_false(self):
        self.assertFalse(self.presence.est_absent)

    def test_est_absent_true(self):
        self.presence.statut = Presence.Statut.ABSENT
        self.assertTrue(self.presence.est_absent)

    def test_est_retard(self):
        self.presence.statut = Presence.Statut.RETARD
        self.assertTrue(self.presence.est_retard)

    def test_unique_together(self):
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Presence.objects.create(
                eleve=self.eleve,
                cours=self.cours,
                classe=self.classe,
                date=date(2026, 10, 15),
                statut=Presence.Statut.ABSENT,
                created_by=self.enseignant,
            )


class AttendanceViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.enseignant = make_user(UserRole.ENSEIGNANT, first_name="Jean", last_name="Prof")
        cls.admin = make_user(UserRole.ADMIN, first_name="Adm", last_name="Att")
        cls.eleve = make_user(UserRole.ELEVE, first_name="Dan", last_name="Elv")
        cls.parent = make_user(UserRole.PARENT, first_name="Par", last_name="Ent")
        cls.classe = make_classe()
        cls.cours = make_cours(classe=cls.classe, enseignant=cls.enseignant)

    def test_saisie_view_enseignant(self):
        self.client.login(email=self.enseignant.email, password=PASSWORD)
        resp = self.client.get(reverse("attendance:saisie"))
        self.assertEqual(resp.status_code, 200)

    def test_saisie_view_with_filters(self):
        self.client.login(email=self.enseignant.email, password=PASSWORD)
        resp = self.client.get(reverse("attendance:saisie"), {
            "classe": str(self.classe.pk),
            "cours": str(self.cours.pk),
            "date": "2026-10-20",
        })
        self.assertEqual(resp.status_code, 200)

    def test_saisie_view_eleve_forbidden(self):
        self.client.login(email=self.eleve.email, password=PASSWORD)
        resp = self.client.get(reverse("attendance:saisie"))
        self.assertEqual(resp.status_code, 403)

    def test_save_presence_htmx(self):
        self.client.login(email=self.enseignant.email, password=PASSWORD)
        resp = self.client.post(reverse("attendance:save"), data={
            "eleve": str(self.eleve.pk),
            "cours": str(self.cours.pk),
            "date": "2026-10-20",
            "statut": "absent",
            "justification": "Maladie",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(
            Presence.objects.filter(
                eleve=self.eleve,
                cours=self.cours,
                date=date(2026, 10, 20),
                statut=Presence.Statut.ABSENT,
            ).exists()
        )

    def test_save_presence_missing_params(self):
        self.client.login(email=self.enseignant.email, password=PASSWORD)
        resp = self.client.post(reverse("attendance:save"), data={
            "eleve": str(self.eleve.pk),
        })
        self.assertEqual(resp.status_code, 400)

    def test_history_view(self):
        self.client.login(email=self.enseignant.email, password=PASSWORD)
        resp = self.client.get(reverse("attendance:history"))
        self.assertEqual(resp.status_code, 200)

    def test_my_attendance_eleve(self):
        self.client.login(email=self.eleve.email, password=PASSWORD)
        resp = self.client.get(reverse("attendance:my_attendance"))
        self.assertEqual(resp.status_code, 200)

    def test_my_attendance_parent_forbidden(self):
        self.client.login(email=self.parent.email, password=PASSWORD)
        resp = self.client.get(reverse("attendance:my_attendance"))
        self.assertEqual(resp.status_code, 403)
