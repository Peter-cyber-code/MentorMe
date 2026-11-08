from datetime import time, timedelta

from django.contrib.admin.sites import AdminSite
from django.core.cache import cache
from django.core.management import call_command
from django.test import RequestFactory
from django.utils import timezone
from rest_framework.test import APITestCase

from booking.models import Availability, Booking
from booking.tests import make_user
from notifications.models import Notification
from profiles.admin import RoleRequestAdmin
from profiles.models import Profile, Role, RoleRequest

LONG = "Je suis consultant en stratégie financière depuis dix ans."


class RoleRequestFlowTests(APITestCase):

    def setUp(self):
        cache.clear()
        self.user = make_user("candidat", "project_owner")
        self.staff = make_user("staff", None)
        self.staff.is_staff = True
        self.staff.is_superuser = True
        self.staff.save()
        self.client.force_authenticate(self.user)

    def _ask(self, role="mentor", message=LONG):
        return self.client.post("/api/profiles/role-requests/", {"role": role, "message": message}, format="json")

    def test_validation_rules(self):
        self.assertEqual(self._ask(message="court").status_code, 400)
        self.assertEqual(self._ask(role="collaborator").status_code, 400)  # rôle libre
        self.assertEqual(self._ask().status_code, 201)
        self.assertEqual(self._ask().status_code, 400)  # déjà en attente

    def test_approval_makes_user_a_bookable_mentor(self):
        self.assertEqual(self._ask().status_code, 201)
        # pas encore dans la liste des mentors
        listing = self.client.get("/api/profiles/?role=mentor&available=true")
        self.assertEqual(listing.data["count"], 0)

        admin = RoleRequestAdmin(RoleRequest, AdminSite())
        admin.message_user = lambda *a, **k: None
        request = RequestFactory().post("/")
        request.user = self.staff
        admin.approve(request, RoleRequest.objects.all())

        profile = Profile.objects.get(user=self.user)
        self.assertTrue(profile.is_verified)
        self.assertTrue(profile.roles.filter(code="mentor").exists())
        self.assertTrue(Notification.objects.filter(recipient=self.user, notification_type="role_approved").exists())
        self.assertEqual(self.client.get("/api/profiles/role-requests/").data[0]["status"], "approved")

        # tarif + disponibilité, puis il apparaît dans la liste et peut recevoir des créneaux
        r = self.client.patch("/api/profiles/me/", {"session_price": "30", "session_duration": 60, "is_available": True}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        listing = self.client.get("/api/profiles/?role=mentor&available=true")
        self.assertEqual(listing.data["count"], 1)
        tomorrow = timezone.localdate() + timedelta(days=1)
        r = self.client.post("/api/booking/availability/", {"date": str(tomorrow), "start_time": "10:00", "end_time": "11:00"}, format="json")
        self.assertEqual(r.status_code, 201, r.data)

    def test_rejection(self):
        self._ask()
        admin = RoleRequestAdmin(RoleRequest, AdminSite())
        admin.message_user = lambda *a, **k: None
        request = RequestFactory().post("/")
        request.user = self.staff
        admin.reject(request, RoleRequest.objects.all())
        self.assertFalse(Profile.objects.get(user=self.user).roles.filter(code="mentor").exists())
        self.assertEqual(self._ask().status_code, 201)  # il peut redemander

    def test_profile_completion(self):
        r = self.client.get("/api/profiles/me/")
        self.assertEqual(r.data["completion"], 0)
        r = self.client.patch("/api/profiles/me/", {"headline": "Fondatrice · Kër Care", "bio": "Santé de proximité", "city": "Abidjan", "country": "Côte d'Ivoire"}, format="json")
        self.assertEqual(r.data["completion"], 67)
        self.assertEqual(r.data["headline"], "Fondatrice · Kër Care")


class AvailabilityManagementTests(APITestCase):

    def test_owner_deletes_free_slot_only(self):
        cache.clear()
        mentor = make_user("m_slots", "mentor", price=20, verified=True)
        client = make_user("c_slots", "project_owner")
        day = timezone.localdate() + timedelta(days=2)
        free = Availability.objects.create(provider=mentor, date=day, start_time=time(9), end_time=time(10))
        taken = Availability.objects.create(provider=mentor, date=day, start_time=time(11), end_time=time(12))
        Booking.objects.create(client=client, provider=mentor, availability=taken, price=20)

        self.client.force_authenticate(client)
        self.assertEqual(self.client.delete(f"/api/booking/availability/{free.id}/").status_code, 403)
        self.client.force_authenticate(mentor)
        self.assertEqual(self.client.delete(f"/api/booking/availability/{taken.id}/").status_code, 400)
        self.assertEqual(self.client.delete(f"/api/booking/availability/{free.id}/").status_code, 204)


class SeedDemoTests(APITestCase):

    def test_seed_is_idempotent_and_usable(self):
        cache.clear()
        call_command("seed_demo", verbosity=0)
        call_command("seed_demo", verbosity=0)
        viewer = make_user("viewer_seed", "project_owner")
        self.client.force_authenticate(viewer)
        mentors = self.client.get("/api/profiles/?role=mentor&available=true")
        self.assertEqual(mentors.data["count"], 3)
        self.assertEqual(self.client.get("/api/calls/").data["count"], 3)
        first = self.client.get("/api/posts/").data["results"]
        self.assertTrue(any(p["project"] for p in first))
        slots = self.client.get(f"/api/booking/providers/{mentors.data['results'][0]['user_id']}/availability/")
        self.assertGreaterEqual(slots.data["count"], 5)


class ProfileMultipartTests(APITestCase):
    """Ce que l'application Flutter envoie : formulaire multipart avec photo et expertises."""

    def test_profile_update_with_photo_and_expertise(self):
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image
        from profiles.models import Expertise
        cache.clear()
        user = make_user("multi", "project_owner")
        a = Expertise.objects.create(name="Finance")
        b = Expertise.objects.create(name="Marketing")
        buf = BytesIO()
        Image.new("RGB", (8, 8), (10, 20, 30)).save(buf, "PNG")
        photo = SimpleUploadedFile("moi.png", buf.getvalue(), content_type="image/png")
        self.client.force_authenticate(user)
        r = self.client.patch(
            "/api/profiles/me/",
            {"headline": "Fondatrice · Kër Care", "bio": "Santé", "city": "Abidjan",
             "country": "Côte d'Ivoire", "expertise_ids": [a.id, b.id], "photo": photo},
            format="multipart",
        )
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["completion"], 100)
        self.assertTrue(r.data["photo"].startswith("http"))
        self.assertEqual(len(r.data["expertise"]), 2)

    def test_register_without_role_gives_project_owner_and_invalid_budget_message(self):
        cache.clear()
        r = self.client.post("/api/accounts/register/", {
            "username": "nouveau@x.com", "email": "nouveau@x.com", "first_name": "Nou", "last_name": "Veau",
            "password": "Xk9#vLm2!qRt7", "password_confirm": "Xk9#vLm2!qRt7"}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(Profile.objects.get(user__email="nouveau@x.com").roles.first().code, "project_owner")
        # un budget saisi avec l'unité est refusé avec un message exploitable
        login = self.client.post("/api/accounts/login/", {"email": "nouveau@x.com", "password": "Xk9#vLm2!qRt7"}, format="json")
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + login.data["access"])
        r = self.client.post("/api/projects/", {"title": "T", "description": "d", "sector": "s", "country": "c",
                                                 "budget": "500000FCFA", "stage": "idea"}, format="multipart")
        self.assertEqual(r.status_code, 400)
        self.assertIn("budget", r.data)


class AdminVisibilityTests(APITestCase):
    """L'administrateur doit voir les demandes de rôle en attente."""

    def test_admin_home_banner_and_changelist(self):
        cache.clear()
        staff = make_user("admin_v", None)
        staff.is_staff = staff.is_superuser = True
        staff.save()
        candidate = make_user("candidat_v", "project_owner")
        candidate.first_name, candidate.last_name = "Moussa", "Traoré"
        candidate.save()
        RoleRequest.objects.create(user=candidate, role=Role.objects.get(code="mentor"), message=LONG)

        self.client.force_login(staff)
        home = self.client.get("/admin/")
        self.assertEqual(home.status_code, 200)
        self.assertContains(home, "demande(s) de rôle")

        listing = self.client.get("/admin/profiles/rolerequest/")
        self.assertEqual(listing.status_code, 200)
        self.assertContains(listing, "Moussa Traoré")
        self.assertContains(listing, "En attente")

        detail = self.client.get(f"/admin/profiles/rolerequest/{RoleRequest.objects.get().id}/change/")
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "Profil du demandeur")

    def test_admin_validates_from_the_changelist(self):
        cache.clear()
        staff = make_user("admin_w", None)
        staff.is_staff = staff.is_superuser = True
        staff.save()
        candidate = make_user("candidat_w", "project_owner")
        rr = RoleRequest.objects.create(user=candidate, role=Role.objects.get(code="mentor"), message=LONG)

        self.client.force_login(staff)
        r = self.client.post(
            "/admin/profiles/rolerequest/",
            {"action": "approve", "_selected_action": [rr.id], "index": "0"},
            follow=True,
        )
        self.assertEqual(r.status_code, 200)
        rr.refresh_from_db()
        self.assertEqual(rr.status, "approved")
        self.assertEqual(rr.reviewed_by, staff)
        self.assertTrue(Profile.objects.get(user=candidate).roles.filter(code="mentor").exists())
