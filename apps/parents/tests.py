from django.test import TestCase
from django.urls import reverse

from apps.accounts.enums import UserRole
from apps.core.test_factories import make_user, PASSWORD
from apps.parents.models import ParentEleve


class ParentEleveModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.parent = make_user(UserRole.PARENT, first_name="Par", last_name="Test")
        cls.eleve = make_user(UserRole.ELEVE, first_name="Kid", last_name="Test")
        cls.liaison = ParentEleve.objects.create(
            parent=cls.parent,
            eleve=cls.eleve,
            relation=ParentEleve.Relation.PERE,
            est_contact_principal=True,
            created_by=cls.parent,
        )

    def test_str(self):
        self.assertIn("Par", str(self.liaison))
        self.assertIn("Kid", str(self.liaison))

    def test_default_autorise_consultation(self):
        self.assertTrue(self.liaison.autorise_consultation)

    def test_unique_together(self):
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            ParentEleve.objects.create(
                parent=self.parent,
                eleve=self.eleve,
                relation=ParentEleve.Relation.MERE,
                created_by=self.parent,
            )


class ParentViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.parent = make_user(UserRole.PARENT, first_name="P", last_name="View")
        cls.eleve = make_user(UserRole.ELEVE, first_name="E", last_name="View")
        cls.admin = make_user(UserRole.ADMIN, first_name="A", last_name="View")
        cls.liaison = ParentEleve.objects.create(
            parent=cls.parent,
            eleve=cls.eleve,
            relation=ParentEleve.Relation.PERE,
            autorise_consultation=True,
            created_by=cls.parent,
        )

    def test_dashboard_parent(self):
        self.client.login(email=self.parent.email, password=PASSWORD)
        resp = self.client.get(reverse("parents:dashboard"))
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_admin_forbidden(self):
        self.client.login(email=self.admin.email, password=PASSWORD)
        resp = self.client.get(reverse("parents:dashboard"))
        self.assertEqual(resp.status_code, 403)

    def test_children_list(self):
        self.client.login(email=self.parent.email, password=PASSWORD)
        resp = self.client.get(reverse("parents:children"))
        self.assertEqual(resp.status_code, 200)

    def test_link_child(self):
        new_eleve = make_user(UserRole.ELEVE, first_name="New", last_name="Kid")
        self.client.login(email=self.parent.email, password=PASSWORD)
        resp = self.client.post(reverse("parents:link_child"), data={
            "eleve": str(new_eleve.pk),
            "relation": "mere",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(
            ParentEleve.objects.filter(parent=self.parent, eleve=new_eleve).exists()
        )

    def test_link_child_duplicate(self):
        self.client.login(email=self.parent.email, password=PASSWORD)
        resp = self.client.post(reverse("parents:link_child"), data={
            "eleve": str(self.eleve.pk),
            "relation": "mere",
        })
        self.assertEqual(resp.status_code, 302)
        # Should not create duplicate
        self.assertEqual(
            ParentEleve.objects.filter(parent=self.parent, eleve=self.eleve).count(),
            1,
        )

    def test_unlink_child(self):
        self.client.login(email=self.parent.email, password=PASSWORD)
        resp = self.client.post(
            reverse("parents:unlink_child", kwargs={"pk": str(self.liaison.pk)})
        )
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(ParentEleve.objects.filter(pk=self.liaison.pk).exists())

    def test_child_bulletins(self):
        self.client.login(email=self.parent.email, password=PASSWORD)
        resp = self.client.get(
            reverse("parents:child_bulletins", kwargs={"eleve_pk": str(self.eleve.pk)})
        )
        self.assertEqual(resp.status_code, 200)

    def test_child_notes(self):
        self.client.login(email=self.parent.email, password=PASSWORD)
        resp = self.client.get(
            reverse("parents:child_notes", kwargs={"eleve_pk": str(self.eleve.pk)})
        )
        self.assertEqual(resp.status_code, 200)

    def test_child_notes_unauthorized_parent(self):
        other_parent = make_user(UserRole.PARENT, first_name="Other", last_name="Parent")
        self.client.login(email=other_parent.email, password=PASSWORD)
        resp = self.client.get(
            reverse("parents:child_notes", kwargs={"eleve_pk": str(self.eleve.pk)})
        )
        self.assertEqual(resp.status_code, 404)
