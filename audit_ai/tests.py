from django.core.cache import cache
from rest_framework.test import APITestCase

from booking.tests import make_user
from profiles.models import Expertise
from projects.models import Project


def make_project(owner, sector="Agriculture"):
    return Project.objects.create(
        owner=owner, title="AgriPlus", description="d", sector=sector,
        country="BF", budget=1000, stage="idea",
    )


def audit_payload(project):
    return {
        "project": project.id, "problem": "p", "solution": "s",
        "target_customers": "t", "business_model": "b",
    }


class AuditTests(APITestCase):

    def setUp(self):
        cache.clear()
        self.owner = make_user("owner", "project_owner")
        self.other = make_user("other", "project_owner")
        self.project = make_project(self.owner)

    def test_audit_runs_with_mock_provider(self):
        self.client.force_authenticate(self.owner)
        r = self.client.post("/api/audits/", audit_payload(self.project), format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["status"], "completed")
        self.assertEqual(r.data["provider"], "mock")
        self.assertIn("scores", r.data["report"])

    def test_cannot_audit_someone_elses_project(self):
        self.client.force_authenticate(self.other)
        r = self.client.post("/api/audits/", audit_payload(self.project), format="json")
        self.assertEqual(r.status_code, 400)

    def test_audit_is_throttled(self):
        self.client.force_authenticate(self.owner)
        codes = [
            self.client.post("/api/audits/", audit_payload(self.project), format="json").status_code
            for _ in range(7)
        ]
        self.assertEqual(codes[:5], [201] * 5)
        self.assertIn(429, codes[5:])

    def test_recommendations_use_audit_needs_and_rank_by_fit(self):
        agri = Expertise.objects.create(name="Agriculture")
        good = make_user("good_mentor", "mentor", price=30, verified=True)
        good.profile.expertise.add(agri)
        weak = make_user("weak_mentor", "mentor", price=30)
        make_user("an_expert", "financial_expert", price=80, verified=True)
        make_user("nobody", "marketing_expert", price=10)  # non demandé par l'audit

        self.client.force_authenticate(self.owner)
        audit_id = self.client.post("/api/audits/", audit_payload(self.project), format="json").data["id"]

        r = self.client.get(f"/api/audits/{audit_id}/recommendations/")
        self.assertEqual(r.status_code, 200, r.data)
        recs = r.data["recommendations"]

        # le mock demande financial_expert + mentor, rien d'autre
        self.assertEqual(set(recs), {"mentor", "financial_expert"})
        mentors = recs["mentor"]
        self.assertEqual(mentors[0]["profile"]["username"], "good_mentor")
        self.assertGreater(mentors[0]["score"], mentors[1]["score"])
        self.assertIn("secteur", mentors[0]["reason"].lower())
        self.assertEqual(mentors[0]["profile"]["user_id"], good.id)
        self.assertTrue(r.data["priority_actions"])

        # confidentialité : un autre utilisateur n'y a pas accès
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(f"/api/audits/{audit_id}/recommendations/").status_code, 404)


class FlutterFacingFieldsTests(APITestCase):
    """Champs dont l'application mobile a besoin pour afficher de vrais noms."""

    def setUp(self):
        cache.clear()

    def test_profile_exposes_rating_and_user_id(self):
        mentor = make_user("m_rate", "mentor", price=30, verified=True)
        type(mentor).objects.filter(pk=mentor.pk).update(rating=4.5)
        self.client.force_authenticate(make_user("viewer", "project_owner"))
        r = self.client.get("/api/profiles/?role=mentor&available=true")
        self.assertEqual(r.status_code, 200)
        item = r.data["results"][0]
        self.assertEqual(item["user_id"], mentor.id)
        self.assertEqual(item["rating"], 4.5)

    def test_conversation_members_and_posts_show_real_names(self):
        from messaging.tests import make_conversation
        a = make_user("na", "project_owner")
        b = make_user("nb", "project_owner")
        for u, first in ((a, "Awa"), (b, "Ibrahima")):
            u.first_name, u.last_name = first, "Test"
            u.save()
        conv = make_conversation(a, b)
        self.client.force_authenticate(a)
        r = self.client.get("/api/messaging/conversations/")
        names = {m["full_name"] for m in r.data["results"][0]["memberships"]}
        self.assertEqual(names, {"Awa Test", "Ibrahima Test"})
        self.assertEqual(conv.id, r.data["results"][0]["id"])
