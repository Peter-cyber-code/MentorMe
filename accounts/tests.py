from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APITestCase

from profiles.models import Profile, Role


STRONG = "Xk9#vLm2!qRt7"


class AuthTests(APITestCase):

    def setUp(self):
        cache.clear()

    def _register(self, **extra):
        data = {
            "username": "alice",
            "email": "alice@example.com",
            "first_name": "Alice",
            "last_name": "A",
            "password": STRONG,
            "password_confirm": STRONG,
        }
        data.update(extra)
        return self.client.post("/api/accounts/register/", data, format="json")

    def test_register_defaults_to_project_owner(self):
        r = self._register()
        self.assertEqual(r.status_code, 201, r.data)
        profile = Profile.objects.get(user__username="alice")
        self.assertEqual(
            set(profile.roles.values_list("code", flat=True)), {"project_owner"}
        )

    def test_register_cannot_choose_privileged_role(self):
        for role in ("mentor", "investor", "financial_expert"):
            cache.clear()
            r = self._register(role=role)
            self.assertEqual(r.status_code, 400, role)

    def test_register_rejects_weak_password(self):
        r = self._register(password="12345678", password_confirm="12345678")
        self.assertEqual(r.status_code, 400)

    def test_login_refresh_rotation_and_logout(self):
        self._register()
        r = self.client.post(
            "/api/accounts/login/",
            {"email": "alice@example.com", "password": STRONG}, format="json",
        )
        self.assertEqual(r.status_code, 200, r.data)
        access, refresh = r.data["access"], r.data["refresh"]

        me = self.client.get("/api/accounts/me/", HTTP_AUTHORIZATION=f"Bearer {access}")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.data["roles"], ["project_owner"])

        r2 = self.client.post("/api/accounts/token/refresh/", {"refresh": refresh}, format="json")
        self.assertEqual(r2.status_code, 200)
        self.assertIn("refresh", r2.data)  # rotation

        # l'ancien refresh est révoqué après rotation
        r3 = self.client.post("/api/accounts/token/refresh/", {"refresh": refresh}, format="json")
        self.assertEqual(r3.status_code, 401)

        # logout révoque le refresh courant
        r4 = self.client.post("/api/accounts/logout/", {"refresh": r2.data["refresh"]}, format="json")
        self.assertEqual(r4.status_code, 200)
        r5 = self.client.post("/api/accounts/token/refresh/", {"refresh": r2.data["refresh"]}, format="json")
        self.assertEqual(r5.status_code, 401)

    def test_login_is_throttled(self):
        statuses = []
        for _ in range(12):
            r = self.client.post(
                "/api/accounts/login/",
                {"email": "x@example.com", "password": "y"}, format="json",
            )
            statuses.append(r.status_code)
        self.assertIn(429, statuses)


class ProfileRoleTests(APITestCase):

    def setUp(self):
        cache.clear()
        from django.contrib.auth import get_user_model
        self.user = get_user_model().objects.create_user("bob", "bob@example.com", STRONG)
        self.client.force_authenticate(self.user)
        self.mentor = Role.objects.get(code="mentor")
        self.collab = Role.objects.get(code="collaborator")

    def test_unverified_cannot_take_mentor_role(self):
        r = self.client.patch("/api/profiles/me/", {"role_ids": [self.mentor.id]}, format="json")
        self.assertEqual(r.status_code, 400, r.data)

    def test_unverified_can_take_collaborator_role(self):
        r = self.client.patch("/api/profiles/me/", {"role_ids": [self.collab.id]}, format="json")
        self.assertEqual(r.status_code, 200, r.data)

    def test_verified_can_take_mentor_role(self):
        Profile.objects.filter(user=self.user).update(is_verified=True)
        r = self.client.patch("/api/profiles/me/", {"role_ids": [self.mentor.id]}, format="json")
        self.assertEqual(r.status_code, 200, r.data)

    def test_cannot_self_verify(self):
        r = self.client.patch("/api/profiles/me/", {"is_verified": True}, format="json")
        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.is_verified)
