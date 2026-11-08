from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APITestCase

from notifications.models import Notification
from profiles.models import Profile, Role
from reviews.models import Review

from .models import Availability, Booking

User = get_user_model()
PW = "Xk9#vLm2!qRt7"


def make_user(name, role=None, price=None, verified=False):
    user = User.objects.create_user(name, f"{name}@example.com", PW)
    profile = user.profile
    profile.is_verified = verified
    profile.is_available = True
    profile.session_price = price
    profile.save()
    if role:
        profile.roles.add(Role.objects.get(code=role))
    return user


class BookingFlowTests(APITestCase):

    def setUp(self):
        cache.clear()
        self.mentor = make_user("mentor", "mentor", price=50, verified=True)
        self.client_user = make_user("client", "project_owner")
        self.stranger = make_user("stranger", "project_owner")
        self.tomorrow = timezone.localdate() + timedelta(days=1)

    def _slot(self, start=time(10), end=time(11), day=None):
        return Availability.objects.create(
            provider=self.mentor, date=day or self.tomorrow,
            start_time=start, end_time=end,
        )

    # --- disponibilités -------------------------------------------------
    def test_only_providers_can_create_availability(self):
        payload = {"date": str(self.tomorrow), "start_time": "10:00", "end_time": "11:00"}
        self.client.force_authenticate(self.client_user)
        self.assertEqual(self.client.post("/api/booking/availability/", payload, format="json").status_code, 403)
        self.client.force_authenticate(self.mentor)
        self.assertEqual(self.client.post("/api/booking/availability/", payload, format="json").status_code, 201)

    def test_availability_rejects_past_and_overlap(self):
        self.client.force_authenticate(self.mentor)
        past = {"date": str(date.today() - timedelta(days=1)), "start_time": "10:00", "end_time": "11:00"}
        self.assertEqual(self.client.post("/api/booking/availability/", past, format="json").status_code, 400)
        self._slot()
        overlap = {"date": str(self.tomorrow), "start_time": "10:30", "end_time": "11:30"}
        self.assertEqual(self.client.post("/api/booking/availability/", overlap, format="json").status_code, 400)

    # --- réservation ----------------------------------------------------
    def test_booking_uses_profile_price_and_notifies_provider(self):
        slot = self._slot()
        self.client.force_authenticate(self.client_user)
        r = self.client.post(f"/api/booking/book/{slot.id}/", {"message": "Hello"}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(float(r.data["price"]), 50.0)
        self.assertTrue(Notification.objects.filter(
            recipient=self.mentor, notification_type="booking_created").exists())

    def test_double_booking_is_refused(self):
        slot = self._slot()
        self.client.force_authenticate(self.client_user)
        self.assertEqual(self.client.post(f"/api/booking/book/{slot.id}/").status_code, 201)
        self.client.force_authenticate(self.stranger)
        self.assertEqual(self.client.post(f"/api/booking/book/{slot.id}/").status_code, 409)

    def test_cannot_book_self_nonprovider_or_past(self):
        slot = self._slot()
        self.client.force_authenticate(self.mentor)
        self.assertEqual(self.client.post(f"/api/booking/book/{slot.id}/").status_code, 400)

        past_slot = self._slot(day=timezone.localdate() - timedelta(days=2))
        self.client.force_authenticate(self.client_user)
        self.assertEqual(self.client.post(f"/api/booking/book/{past_slot.id}/").status_code, 400)

        Profile.objects.filter(user=self.mentor).update(session_price=None)
        self.assertEqual(self.client.post(f"/api/booking/book/{slot.id}/").status_code, 400)

    def test_listed_slots_exclude_booked_ones(self):
        slot = self._slot()
        self.client.force_authenticate(self.client_user)
        self.client.post(f"/api/booking/book/{slot.id}/")
        r = self.client.get(f"/api/booking/providers/{self.mentor.id}/availability/")
        self.assertEqual(r.data["count"], 0)

    # --- cycle de vie + avis -------------------------------------------
    def _booked(self, day=None):
        slot = self._slot(day=day)
        return Booking.objects.create(
            client=self.client_user, provider=self.mentor,
            availability=slot, price=50,
        )

    def test_full_lifecycle_then_review_updates_rating(self):
        booking = self._booked()

        # seul le prestataire agit
        self.client.force_authenticate(self.client_user)
        self.assertEqual(self.client.post(f"/api/booking/{booking.id}/confirm/").status_code, 404)

        self.client.force_authenticate(self.mentor)
        self.assertEqual(self.client.post(f"/api/booking/{booking.id}/confirm/").status_code, 200)
        # session future : pas de clôture possible
        self.assertEqual(self.client.post(f"/api/booking/{booking.id}/complete/").status_code, 400)

        # on simule le passage du temps
        Availability.objects.filter(pk=booking.availability_id).update(
            date=timezone.localdate() - timedelta(days=1))
        self.assertEqual(self.client.post(f"/api/booking/{booking.id}/complete/").status_code, 200)

        # avis : seulement le client, une seule fois
        self.client.force_authenticate(self.stranger)
        self.assertEqual(self.client.post("/api/reviews/", {"booking": booking.id, "rating": 5}, format="json").status_code, 400)

        self.client.force_authenticate(self.client_user)
        r = self.client.post("/api/reviews/", {"booking": booking.id, "rating": 4, "comment": "Top"}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["professional"], self.mentor.id)
        self.assertEqual(self.client.post("/api/reviews/", {"booking": booking.id, "rating": 5}, format="json").status_code, 400)

        self.mentor.refresh_from_db()
        self.assertEqual(self.mentor.rating, 4)
        self.assertTrue(Notification.objects.filter(recipient=self.mentor, notification_type="review").exists())

        # modification d'avis (booking ignoré) → moyenne recalculée
        review = Review.objects.get(booking=booking)
        r = self.client.patch(f"/api/reviews/{review.id}/", {"rating": 2}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.mentor.refresh_from_db()
        self.assertEqual(self.mentor.rating, 2)

    def test_review_refused_before_completion(self):
        booking = self._booked()
        self.client.force_authenticate(self.client_user)
        r = self.client.post("/api/reviews/", {"booking": booking.id, "rating": 5}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_reject_and_cancel_rules(self):
        booking = self._booked()
        self.client.force_authenticate(self.mentor)
        self.assertEqual(self.client.post(f"/api/booking/{booking.id}/reject/").status_code, 200)
        # une réservation refusée ne peut plus être annulée ni confirmée
        self.assertEqual(self.client.post(f"/api/booking/{booking.id}/cancel/").status_code, 400)
        self.assertEqual(self.client.post(f"/api/booking/{booking.id}/confirm/").status_code, 400)

        # un tiers ne voit même pas la réservation
        b2 = self._booked(day=self.tomorrow + timedelta(days=1))
        self.client.force_authenticate(self.stranger)
        self.assertEqual(self.client.post(f"/api/booking/{b2.id}/cancel/").status_code, 404)

        # le client peut annuler, le créneau redevient libre
        self.client.force_authenticate(self.client_user)
        self.assertEqual(self.client.post(f"/api/booking/{b2.id}/cancel/").status_code, 200)
        self.client.force_authenticate(self.stranger)
        self.assertEqual(self.client.post(f"/api/booking/book/{b2.availability_id}/").status_code, 201)
