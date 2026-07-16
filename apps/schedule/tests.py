from datetime import time

from django.test import TestCase
from django.urls import reverse

from apps.accounts.enums import UserRole
from apps.core.test_factories import (
    make_annee, make_classe, make_cours, make_user, PASSWORD,
)
from apps.schedule.models import Creneau


class CreneauModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.annee = make_annee()
        cls.enseignant = make_user(UserRole.ENSEIGNANT, first_name="Sched", last_name="Prof")
        cls.classe = make_classe()
        cls.cours = make_cours(classe=cls.classe, enseignant=cls.enseignant)
        cls.creneau = Creneau.objects.create(
            classe=cls.classe,
            cours=cls.cours,
            enseignant=cls.enseignant,
            jour=Creneau.Jour.LUNDI,
            heure_debut=time(8, 0),
            heure_fin=time(10, 0),
            salle="A1",
            annee_scolaire=cls.annee,
            created_by=cls.enseignant,
        )

    def test_str(self):
        self.assertIn("5ème A", str(self.creneau))

    def test_duree_minutes(self):
        self.assertEqual(self.creneau.duree_minutes, 120)

    def test_detecter_conflits_none(self):
        conflits = self.creneau.detecter_conflits(exclude_pk=self.creneau.pk)
        self.assertEqual(len(conflits), 0)

    def test_detecter_conflits_enseignant(self):
        classe2 = make_classe(nom="6ème B")
        cours2 = make_cours(classe=classe2, code="PHY", enseignant=self.enseignant)
        creneau2 = Creneau(
            classe=classe2,
            cours=cours2,
            enseignant=self.enseignant,
            jour=Creneau.Jour.LUNDI,
            heure_debut=time(9, 0),
            heure_fin=time(11, 0),
            annee_scolaire=self.annee,
        )
        conflits = creneau2.detecter_conflits()
        types = [c["type"] for c in conflits]
        self.assertIn("enseignant", types)

    def test_detecter_conflits_classe(self):
        cours2 = make_cours(classe=self.classe, code="CHIM", enseignant=self.enseignant)
        creneau2 = Creneau(
            classe=self.classe,
            cours=cours2,
            enseignant=self.enseignant,
            jour=Creneau.Jour.LUNDI,
            heure_debut=time(9, 0),
            heure_fin=time(11, 0),
            annee_scolaire=self.annee,
        )
        conflits = creneau2.detecter_conflits()
        types = [c["type"] for c in conflits]
        self.assertIn("classe", types)

    def test_unique_together(self):
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Creneau.objects.create(
                classe=self.classe,
                cours=self.cours,
                enseignant=self.enseignant,
                jour=Creneau.Jour.LUNDI,
                heure_debut=time(8, 0),
                heure_fin=time(10, 0),
                annee_scolaire=self.annee,
                created_by=self.enseignant,
            )


class ScheduleViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = make_user(UserRole.ADMIN, first_name="Adm", last_name="Sched")
        cls.enseignant = make_user(UserRole.ENSEIGNANT, first_name="Ens", last_name="Sched")
        cls.eleve = make_user(UserRole.ELEVE, first_name="Elv", last_name="Sched")
        cls.annee = make_annee()
        cls.classe = make_classe()
        cls.cours = make_cours(classe=cls.classe, enseignant=cls.enseignant)

    def test_timetable_view_admin(self):
        self.client.login(email=self.admin.email, password=PASSWORD)
        resp = self.client.get(reverse("schedule:timetable"))
        self.assertEqual(resp.status_code, 200)

    def test_timetable_view_eleve(self):
        self.client.login(email=self.eleve.email, password=PASSWORD)
        resp = self.client.get(reverse("schedule:timetable"))
        self.assertEqual(resp.status_code, 200)

    def test_create_creneau(self):
        self.client.login(email=self.admin.email, password=PASSWORD)
        resp = self.client.post(reverse("schedule:creneau_create"), data={
            "classe": str(self.classe.pk),
            "cours": str(self.cours.pk),
            "enseignant": str(self.enseignant.pk),
            "jour": "mardi",
            "heure_debut": "10:00",
            "heure_fin": "12:00",
            "annee_scolaire": str(self.annee.pk),
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(
            Creneau.objects.filter(jour="mardi", heure_debut=time(10, 0)).exists()
        )

    def test_delete_creneau(self):
        creneau = Creneau.objects.create(
            classe=self.classe,
            cours=self.cours,
            enseignant=self.enseignant,
            jour=Creneau.Jour.MERCREDI,
            heure_debut=time(14, 0),
            heure_fin=time(16, 0),
            annee_scolaire=self.annee,
            created_by=self.admin,
        )
        self.client.login(email=self.admin.email, password=PASSWORD)
        resp = self.client.post(reverse("schedule:creneau_delete", kwargs={"pk": str(creneau.pk)}))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Creneau.objects.filter(pk=creneau.pk).exists())

    def test_conflict_check(self):
        Creneau.objects.create(
            classe=self.classe,
            cours=self.cours,
            enseignant=self.enseignant,
            jour=Creneau.Jour.VENDREDI,
            heure_debut=time(8, 0),
            heure_fin=time(10, 0),
            annee_scolaire=self.annee,
            created_by=self.admin,
        )
        self.client.login(email=self.admin.email, password=PASSWORD)
        resp = self.client.get(reverse("schedule:conflit_check"), {
            "classe": str(self.classe.pk),
            "enseignant": str(self.enseignant.pk),
            "jour": "vendredi",
            "heure_debut": "09:00",
            "heure_fin": "11:00",
            "annee_scolaire": str(self.annee.pk),
        })
        self.assertEqual(resp.status_code, 200)
