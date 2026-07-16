from decimal import Decimal
from datetime import date

from django.test import TestCase
from django.urls import reverse

from apps.accounts.enums import UserRole
from apps.core.test_factories import (
    make_annee, make_user, PASSWORD,
)
from apps.finance.models import FraisEleve, FraisType, Paiement


class FinanceModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.annee = make_annee()
        cls.admin = make_user(UserRole.ADMIN, first_name="Admin", last_name="Fin")
        cls.eleve = make_user(UserRole.ELEVE, first_name="Bob", last_name="Eleve")
        cls.frais_type = FraisType.objects.create(
            libelle="Minerval 1er terme",
            categorie=FraisType.Categorie.SCOLARITE,
            montant=Decimal("150.00"),
            annee_scolaire=cls.annee,
            created_by=cls.admin,
        )
        cls.frais_eleve = FraisEleve.objects.create(
            eleve=cls.eleve,
            frais_type=cls.frais_type,
            annee_scolaire=cls.annee,
            montant_total=Decimal("150.00"),
            date_echeance=date(2026, 10, 31),
            created_by=cls.admin,
        )

    def test_frais_type_str(self):
        self.assertIn("Minerval", str(self.frais_type))

    def test_frais_eleve_str(self):
        self.assertIn("Bob", str(self.frais_eleve))

    def test_montant_restant(self):
        self.assertEqual(self.frais_eleve.montant_restant, Decimal("150.00"))

    def test_est_solde_false(self):
        self.assertFalse(self.frais_eleve.est_solde)

    def test_pourcentage_paye_zero(self):
        self.assertEqual(self.frais_eleve.pourcentage_paye, 0)

    def test_enregistrer_paiement(self):
        paiement = self.frais_eleve.enregistrer_paiement(
            montant=Decimal("50.00"),
            methode=Paiement.Methode.ESPECES,
            enregistre_par=self.admin,
        )
        self.frais_eleve.refresh_from_db()
        self.assertEqual(self.frais_eleve.montant_paye, Decimal("50.00"))
        self.assertEqual(self.frais_eleve.statut, FraisEleve.Statut.PARTIELLEMENT_PAYE)
        self.assertEqual(paiement.montant, Decimal("50.00"))

    def test_paiement_complet_solde(self):
        self.frais_eleve.enregistrer_paiement(
            montant=Decimal("150.00"),
            enregistre_par=self.admin,
        )
        self.frais_eleve.refresh_from_db()
        self.assertTrue(self.frais_eleve.est_solde)
        self.assertEqual(self.frais_eleve.statut, FraisEleve.Statut.PAYE)

    def test_mettre_a_jour_statut_retard(self):
        frais = FraisEleve.objects.create(
            eleve=make_user(UserRole.ELEVE, first_name="Late", last_name="Student"),
            frais_type=self.frais_type,
            annee_scolaire=self.annee,
            montant_total=Decimal("100.00"),
            date_echeance=date(2020, 1, 1),
            created_by=self.admin,
        )
        frais.mettre_a_jour_statut()
        self.assertEqual(frais.statut, FraisEleve.Statut.EN_RETARD)

    def test_paiement_code(self):
        paiement = self.frais_eleve.enregistrer_paiement(
            montant=Decimal("10.00"),
            enregistre_par=self.admin,
        )
        self.assertTrue(paiement.code.startswith("PAY-"))


class FinanceViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = make_user(UserRole.ADMIN, first_name="Admin", last_name="View")
        cls.eleve = make_user(UserRole.ELEVE, first_name="Eve", last_name="Student")
        cls.annee = make_annee()
        cls.frais_type = FraisType.objects.create(
            libelle="Frais test",
            categorie=FraisType.Categorie.SCOLARITE,
            montant=Decimal("100.00"),
            annee_scolaire=cls.annee,
            created_by=cls.admin,
        )

    def setUp(self):
        self.client.login(email=self.admin.email, password=PASSWORD)

    def test_dashboard_access(self):
        resp = self.client.get(reverse("finance:dashboard"))
        self.assertEqual(resp.status_code, 200)

    def test_frais_type_list(self):
        resp = self.client.get(reverse("finance:frais_type_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Frais test")

    def test_frais_type_create(self):
        resp = self.client.post(reverse("finance:frais_type_create"), data={
            "libelle": "Nouveau frais",
            "categorie": "examen",
            "montant": "200",
            "annee_scolaire": str(self.annee.pk),
            "est_obligatoire": "on",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(FraisType.objects.filter(libelle="Nouveau frais").exists())

    def test_frais_eleve_list(self):
        resp = self.client.get(reverse("finance:frais_eleve_list"))
        self.assertEqual(resp.status_code, 200)

    def test_frais_eleve_list_htmx(self):
        resp = self.client.get(
            reverse("finance:frais_eleve_list"),
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(resp.status_code, 200)

    def test_paiement_list(self):
        resp = self.client.get(reverse("finance:paiement_list"))
        self.assertEqual(resp.status_code, 200)

    def test_role_restriction_eleve(self):
        self.client.logout()
        self.client.login(email=self.eleve.email, password=PASSWORD)
        resp = self.client.get(reverse("finance:dashboard"))
        self.assertEqual(resp.status_code, 403)

    def test_frais_assign(self):
        resp = self.client.post(reverse("finance:frais_assign"), data={
            "frais_type": str(self.frais_type.pk),
            "date_echeance": "2026-12-31",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(
            FraisEleve.objects.filter(
                eleve=self.eleve, frais_type=self.frais_type
            ).exists()
        )
