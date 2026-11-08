from datetime import timedelta

from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APITestCase

from booking.tests import make_user
from calls.models import ProjectCall
from projects.models import Project


class CallTests(APITestCase):

    def setUp(self):
        cache.clear()
        today = timezone.localdate()
        self.grant = ProjectCall.objects.create(title="Fonds A", organization="Fondation", category="subvention", deadline=today + timedelta(days=20))
        self.contest = ProjectCall.objects.create(title="Prix B", organization="Africa Forward", category="concours", deadline=today + timedelta(days=5))
        ProjectCall.objects.create(title="Expiré", organization="X", deadline=today - timedelta(days=1))
        ProjectCall.objects.create(title="Brouillon", organization="X", is_published=False)
        self.user = make_user("candidate", "project_owner")
        self.other = make_user("other_c", "project_owner")
        self.project = Project.objects.create(owner=self.user, title="AgriPlus", description="d", sector="Agri", country="BF", budget=1, stage="idea")
        self.client.force_authenticate(self.user)

    def test_only_open_published_calls_sorted_by_deadline(self):
        r = self.client.get("/api/calls/")
        self.assertEqual([c["title"] for c in r.data["results"]], ["Prix B", "Fonds A"])
        r = self.client.get("/api/calls/?category=subvention")
        self.assertEqual([c["title"] for c in r.data["results"]], ["Fonds A"])
        self.assertEqual(r.data["results"][0]["category_label"], "Subvention")

    def test_save_toggle_and_saved_list(self):
        self.assertEqual(self.client.post(f"/api/calls/{self.grant.id}/save/").data["saved"], True)
        self.assertTrue(self.client.get("/api/calls/").data["results"][1]["saved"])
        self.assertEqual(self.client.get("/api/calls/saved/").data["count"], 1)
        self.assertEqual(self.client.post(f"/api/calls/{self.grant.id}/save/").data["saved"], False)

    def test_apply_rules(self):
        url = f"/api/calls/{self.contest.id}/apply/"
        foreign = Project.objects.create(owner=self.other, title="Autre", description="d", sector="x", country="BF", budget=1, stage="idea")
        self.assertEqual(self.client.post(url, {"project": foreign.id}, format="json").status_code, 400)
        r = self.client.post(url, {"project": self.project.id, "message": "Candidature"}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(self.client.post(url, {"project": self.project.id}, format="json").status_code, 400)  # déjà postulé
        self.assertTrue(self.client.get("/api/calls/").data["results"][0]["applied"])
