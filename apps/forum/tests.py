from django.test import TestCase
from django.urls import reverse

from apps.accounts.enums import UserRole
from apps.core.test_factories import (
    make_cours, make_classe, make_user, PASSWORD,
)
from apps.forum.models import Question, Reponse


class ForumModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.eleve = make_user(UserRole.ELEVE, first_name="Q", last_name="Asker")
        cls.enseignant = make_user(UserRole.ENSEIGNANT, first_name="A", last_name="Answerer")
        cls.classe = make_classe()
        cls.cours = make_cours(classe=cls.classe, enseignant=cls.enseignant)
        cls.question = Question.objects.create(
            titre="Comment résoudre x²+1=0 ?",
            contenu="Je ne comprends pas les nombres complexes.",
            auteur=cls.eleve,
            cours=cls.cours,
            created_by=cls.eleve,
        )

    def test_question_str(self):
        self.assertIn("x²", str(self.question))

    def test_question_default_statut(self):
        self.assertEqual(self.question.statut, Question.Statut.OUVERTE)

    def test_question_nb_reponses_zero(self):
        self.assertEqual(self.question.nb_reponses, 0)

    def test_reponse_auto_status_change(self):
        r = Reponse.objects.create(
            question=self.question,
            auteur=self.enseignant,
            contenu="Utilisez i = sqrt(-1).",
            created_by=self.enseignant,
        )
        self.question.refresh_from_db()
        self.assertEqual(self.question.statut, Question.Statut.REPONDUE)

    def test_reponse_validee(self):
        r = Reponse.objects.create(
            question=self.question,
            auteur=self.enseignant,
            contenu="Bonne réponse",
            created_by=self.enseignant,
        )
        r.est_validee = True
        r.save()
        self.assertTrue(r.est_validee)

    def test_a_une_reponse_enseignant(self):
        Reponse.objects.create(
            question=self.question,
            auteur=self.enseignant,
            contenu="Test",
            created_by=self.enseignant,
        )
        self.assertTrue(self.question.a_une_reponse_enseignant)


class ForumViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.eleve = make_user(UserRole.ELEVE, first_name="Forum", last_name="Eleve")
        cls.enseignant = make_user(UserRole.ENSEIGNANT, first_name="Forum", last_name="Prof")
        cls.parent = make_user(UserRole.PARENT, first_name="Forum", last_name="Parent")
        cls.classe = make_classe()
        cls.cours = make_cours(classe=cls.classe, enseignant=cls.enseignant)

    def test_question_list_eleve(self):
        self.client.login(email=self.eleve.email, password=PASSWORD)
        resp = self.client.get(reverse("forum:question_list"))
        self.assertEqual(resp.status_code, 200)

    def test_question_list_enseignant(self):
        self.client.login(email=self.enseignant.email, password=PASSWORD)
        resp = self.client.get(reverse("forum:question_list"))
        self.assertEqual(resp.status_code, 200)

    def test_question_list_htmx(self):
        self.client.login(email=self.eleve.email, password=PASSWORD)
        resp = self.client.get(
            reverse("forum:question_list"),
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(resp.status_code, 200)

    def test_question_create(self):
        self.client.login(email=self.eleve.email, password=PASSWORD)
        resp = self.client.post(reverse("forum:question_create"), data={
            "titre": "Question test",
            "contenu": "Ceci est une question de test.",
            "cours": str(self.cours.pk),
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Question.objects.filter(titre="Question test").exists())

    def test_question_create_empty_rejected(self):
        self.client.login(email=self.eleve.email, password=PASSWORD)
        resp = self.client.post(reverse("forum:question_create"), data={
            "titre": "",
            "contenu": "",
        })
        self.assertEqual(resp.status_code, 302)
        # Message d'erreur dans session, pas de création
        self.assertFalse(Question.objects.filter(titre="").exists())

    def test_question_create_enseignant_forbidden(self):
        self.client.login(email=self.enseignant.email, password=PASSWORD)
        resp = self.client.post(reverse("forum:question_create"), data={
            "titre": "Test",
            "contenu": "Test",
        })
        self.assertEqual(resp.status_code, 403)

    def test_question_detail(self):
        q = Question.objects.create(
            titre="Detail test",
            contenu="Contenu test",
            auteur=self.eleve,
            created_by=self.eleve,
        )
        self.client.login(email=self.enseignant.email, password=PASSWORD)
        resp = self.client.get(reverse("forum:question_detail", kwargs={"pk": str(q.pk)}))
        self.assertEqual(resp.status_code, 200)

    def test_reponse_create_htmx(self):
        q = Question.objects.create(
            titre="Reponse test",
            contenu="Contenu",
            auteur=self.eleve,
            created_by=self.eleve,
        )
        self.client.login(email=self.enseignant.email, password=PASSWORD)
        resp = self.client.post(
            reverse("forum:reponse_create", kwargs={"pk": str(q.pk)}),
            data={"contenu": "Voici ma réponse."},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Reponse.objects.filter(question=q).exists())

    def test_reponse_validate_by_author(self):
        q = Question.objects.create(
            titre="Validate test",
            contenu="Contenu",
            auteur=self.eleve,
            created_by=self.eleve,
        )
        r = Reponse.objects.create(
            question=q,
            auteur=self.enseignant,
            contenu="Bonne rep",
            created_by=self.enseignant,
        )
        self.client.login(email=self.eleve.email, password=PASSWORD)
        resp = self.client.post(reverse("forum:reponse_validate", kwargs={"pk": str(r.pk)}))
        self.assertEqual(resp.status_code, 302)
        r.refresh_from_db()
        self.assertTrue(r.est_validee)

    def test_question_close(self):
        q = Question.objects.create(
            titre="Close test",
            contenu="Contenu",
            auteur=self.eleve,
            created_by=self.eleve,
        )
        self.client.login(email=self.eleve.email, password=PASSWORD)
        resp = self.client.post(reverse("forum:question_close", kwargs={"pk": str(q.pk)}))
        self.assertEqual(resp.status_code, 302)
        q.refresh_from_db()
        self.assertEqual(q.statut, Question.Statut.FERMEE)

    def test_parent_cannot_access_forum(self):
        self.client.login(email=self.parent.email, password=PASSWORD)
        resp = self.client.get(reverse("forum:question_list"))
        self.assertEqual(resp.status_code, 403)
