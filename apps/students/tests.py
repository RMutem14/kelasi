from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.accounts.enums import UserRole
from apps.core.test_factories import (
    make_annee, make_classe, make_cours, make_evaluation,
    make_periode, make_user, PASSWORD,
)
from apps.students.models import Bulletin, Note
from apps.students.services import BulletinGenerator, publish_bulletin


class NoteModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.eleve = make_user(UserRole.ELEVE, first_name="Note", last_name="Eleve")
        cls.enseignant = make_user(UserRole.ENSEIGNANT, first_name="Note", last_name="Prof")
        cls.classe = make_classe()
        cls.cours = make_cours(classe=cls.classe, enseignant=cls.enseignant)
        cls.eval = make_evaluation(cours=cls.cours, classe=cls.classe, enseignant=cls.enseignant)
        cls.note = Note.objects.create(
            eleve=cls.eleve,
            evaluation=cls.eval,
            valeur=Decimal("15.50"),
            created_by=cls.enseignant,
        )

    def test_str(self):
        self.assertIn("15.50", str(self.note))

    def test_pourcentage(self):
        self.assertEqual(self.note.pourcentage, 77.5)

    def test_mention_bien(self):
        self.assertEqual(self.note.mention, "Bien")

    def test_mention_tres_bien(self):
        self.note.valeur = Decimal("18.00")
        self.assertEqual(self.note.mention, "Très bien")

    def test_mention_insuffisant(self):
        self.note.valeur = Decimal("5.00")
        self.assertEqual(self.note.mention, "Insuffisant")


class BulletinModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.eleve = make_user(UserRole.ELEVE, first_name="Bull", last_name="Eleve")
        cls.admin = make_user(UserRole.ADMIN, first_name="Bull", last_name="Admin")
        cls.annee = make_annee()
        cls.classe = make_classe(annee=cls.annee)
        cls.periode = make_periode(annee=cls.annee)
        cls.bulletin = Bulletin.objects.create(
            eleve=cls.eleve,
            classe=cls.classe,
            periode=cls.periode,
            annee_scolaire=cls.annee,
            moyenne_generale=Decimal("14.50"),
            created_by=cls.admin,
        )

    def test_str(self):
        self.assertIn("Bull", str(self.bulletin))

    def test_mention_bien(self):
        self.assertEqual(self.bulletin.mention, "Bien")

    def test_mention_tres_bien(self):
        self.bulletin.moyenne_generale = Decimal("17.00")
        self.assertEqual(self.bulletin.mention, "Très Bien")

    def test_mention_assez_bien(self):
        self.bulletin.moyenne_generale = Decimal("12.50")
        self.assertEqual(self.bulletin.mention, "Assez Bien")

    def test_est_publie_false(self):
        self.assertFalse(self.bulletin.est_publie)

    def test_pourcentage(self):
        self.assertEqual(self.bulletin.pourcentage, 72.5)

    def test_calculer_moyenne_empty(self):
        self.bulletin.lignes.all().delete()
        self.bulletin.calculer_moyenne()
        self.assertEqual(self.bulletin.moyenne_generale, Decimal("0"))


class BulletinGeneratorTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.eleve = make_user(UserRole.ELEVE, first_name="Gen", last_name="Eleve")
        cls.enseignant = make_user(UserRole.ENSEIGNANT, first_name="Gen", last_name="Prof")
        cls.annee = make_annee()
        cls.classe = make_classe(annee=cls.annee)
        cls.cours = make_cours(classe=cls.classe, coef=2, enseignant=cls.enseignant)
        cls.periode = make_periode(annee=cls.annee)
        cls.eval = make_evaluation(cours=cls.cours, classe=cls.classe, enseignant=cls.enseignant)
        cls.note = Note.objects.create(
            eleve=cls.eleve,
            evaluation=cls.eval,
            valeur=Decimal("16.00"),
            created_by=cls.enseignant,
        )

    def test_generate_bulletin(self):
        gen = BulletinGenerator(self.eleve, self.classe, self.periode)
        bulletin = gen.generate(publie_par=self.enseignant)
        self.assertEqual(bulletin.eleve, self.eleve)
        self.assertTrue(bulletin.lignes.exists())
        ligne = bulletin.lignes.first()
        self.assertEqual(ligne.cours, self.cours)
        self.assertEqual(ligne.coefficient, 2)

    def test_generate_appreciation(self):
        appreciation = BulletinGenerator._generer_appreciation(Decimal("17.00"))
        self.assertIn("Très bon", appreciation)

    def test_generate_appreciation_insuffisant(self):
        appreciation = BulletinGenerator._generer_appreciation(Decimal("5.00"))
        self.assertIn("insuffisant", appreciation.lower())


class PublishBulletinTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.eleve = make_user(UserRole.ELEVE, first_name="Pub", last_name="Eleve")
        cls.admin = make_user(UserRole.ADMIN, first_name="Pub", last_name="Admin")
        cls.annee = make_annee()
        cls.classe = make_classe(annee=cls.annee)
        cls.periode = make_periode(annee=cls.annee)
        cls.bulletin = Bulletin.objects.create(
            eleve=cls.eleve,
            classe=cls.classe,
            periode=cls.periode,
            annee_scolaire=cls.annee,
            created_by=cls.admin,
        )

    def test_publish_bulletin(self):
        publish_bulletin(self.bulletin, self.admin)
        self.bulletin.refresh_from_db()
        self.assertEqual(self.bulletin.statut, Bulletin.Statut.PUBLIE)
        self.assertIsNotNone(self.bulletin.date_publication)
        self.assertEqual(self.bulletin.publie_par, self.admin)


class StudentViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.eleve = make_user(UserRole.ELEVE, first_name="View", last_name="Eleve")
        cls.admin = make_user(UserRole.ADMIN, first_name="View", last_name="Admin")
        cls.parent = make_user(UserRole.PARENT, first_name="View", last_name="Parent")
        cls.annee = make_annee()
        cls.classe = make_classe(annee=cls.annee)
        cls.periode = make_periode(annee=cls.annee)

    def test_my_notes_eleve(self):
        self.client.login(email=self.eleve.email, password=PASSWORD)
        resp = self.client.get(reverse("students:notes"))
        self.assertEqual(resp.status_code, 200)

    def test_my_notes_parent_forbidden(self):
        self.client.login(email=self.parent.email, password=PASSWORD)
        resp = self.client.get(reverse("students:notes"))
        self.assertEqual(resp.status_code, 403)

    def test_my_bulletins_eleve(self):
        self.client.login(email=self.eleve.email, password=PASSWORD)
        resp = self.client.get(reverse("students:my_bulletins"))
        self.assertEqual(resp.status_code, 200)

    def test_bulletin_list_admin(self):
        self.client.login(email=self.admin.email, password=PASSWORD)
        resp = self.client.get(reverse("students:bulletin_list"))
        self.assertEqual(resp.status_code, 200)

    def test_bulletin_list_htmx(self):
        self.client.login(email=self.admin.email, password=PASSWORD)
        resp = self.client.get(
            reverse("students:bulletin_list"),
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(resp.status_code, 200)

    def test_periode_list_admin(self):
        self.client.login(email=self.admin.email, password=PASSWORD)
        resp = self.client.get(reverse("students:periode_list"))
        self.assertEqual(resp.status_code, 200)

    def test_bulletin_viewer_admin(self):
        bulletin = Bulletin.objects.create(
            eleve=self.eleve,
            classe=self.classe,
            periode=self.periode,
            annee_scolaire=self.annee,
            created_by=self.admin,
        )
        self.client.login(email=self.admin.email, password=PASSWORD)
        resp = self.client.get(reverse("students:bulletin_viewer", kwargs={"pk": str(bulletin.pk)}))
        self.assertEqual(resp.status_code, 200)
