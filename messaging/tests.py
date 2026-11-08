from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.core.cache import cache
from django.test import TransactionTestCase
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from booking.tests import make_user
from config.asgi import application
from notifications.models import Notification

from .models import Conversation, ConversationParticipant


def make_conversation(a, b):
    conv = Conversation.objects.create(conversation_type="private", created_by=a)
    ConversationParticipant.objects.create(conversation=conv, user=a)
    ConversationParticipant.objects.create(conversation=conv, user=b)
    return conv


class RestMessagingTests(APITestCase):

    def setUp(self):
        cache.clear()
        self.a = make_user("a", "project_owner")
        self.b = make_user("b", "project_owner")
        self.c = make_user("c", "project_owner")
        self.conv = make_conversation(self.a, self.b)

    def test_rest_message_creates_notification_and_is_private(self):
        self.client.force_authenticate(self.a)
        r = self.client.post(f"/api/messaging/conversations/{self.conv.id}/messages/send/",
                             {"content": "salut"}, format="json")
        self.assertIn(r.status_code, (200, 201), r.data if hasattr(r, "data") else None)
        self.assertTrue(Notification.objects.filter(recipient=self.b, notification_type="message").exists())
        self.assertFalse(Notification.objects.filter(recipient=self.a).exists())

        self.client.force_authenticate(self.c)
        r = self.client.get(f"/api/messaging/conversations/{self.conv.id}/messages/")
        self.assertEqual(r.status_code, 403)


class WebSocketJWTTests(TransactionTestCase):

    def _communicator(self, conv, token=None):
        suffix = f"?token={token}" if token else ""
        return WebsocketCommunicator(application, f"/ws/messaging/{conv.id}/{suffix}")

    def setUp(self):
        self.a = make_user("wa", "project_owner")
        self.b = make_user("wb", "project_owner")
        self.c = make_user("wc", "project_owner")
        self.conv = make_conversation(self.a, self.b)

    def test_ws_requires_valid_jwt_and_membership(self):
        async def run():
            no_token = self._communicator(self.conv)
            ok, _ = await no_token.connect()
            self.assertFalse(ok)

            bad = self._communicator(self.conv, "not-a-token")
            ok, _ = await bad.connect()
            self.assertFalse(ok)

            outsider = self._communicator(self.conv, str(AccessToken.for_user(self.c)))
            ok, _ = await outsider.connect()
            self.assertFalse(ok)

            member = self._communicator(self.conv, str(AccessToken.for_user(self.a)))
            ok, _ = await member.connect()
            self.assertTrue(ok)

            await member.send_json_to({"content": "bonjour"})
            reply = await member.receive_json_from()
            self.assertEqual(reply["content"], "bonjour")
            self.assertEqual(reply["sender"], self.a.id)
            await member.disconnect()

        async_to_sync(run)()
        self.assertTrue(Notification.objects.filter(recipient=self.b, notification_type="message").exists())


class AttachmentTests(APITestCase):

    def setUp(self):
        cache.clear()
        self.a = make_user("att_a", "project_owner")
        self.b = make_user("att_b", "project_owner")
        self.conv = make_conversation(self.a, self.b)
        self.client.force_authenticate(self.a)
        self.url = f"/api/messaging/conversations/{self.conv.id}/messages/send/"

    def _file(self, name, data=b"contenu"):
        from django.core.files.uploadedfile import SimpleUploadedFile
        return SimpleUploadedFile(name, data)

    def test_attachment_only_message(self):
        r = self.client.post(self.url, {"attachments": [self._file("plan.pdf"), self._file("photo.png")]}, format="multipart")
        self.assertEqual(r.status_code, 201, r.data)
        names = sorted(a["file_name"] for a in r.data["attachments"])
        self.assertEqual(names, ["photo.png", "plan.pdf"])
        self.assertTrue(r.data["attachments"][0]["file"].startswith("http"))

    def test_empty_message_and_dangerous_file_are_refused(self):
        self.assertEqual(self.client.post(self.url, {"content": "  "}, format="multipart").status_code, 400)
        r = self.client.post(self.url, {"attachments": [self._file("virus.exe")]}, format="multipart")
        self.assertEqual(r.status_code, 400)
        too_big = self._file("gros.pdf", b"x" * (11 * 1024 * 1024))
        self.assertEqual(self.client.post(self.url, {"attachments": [too_big]}, format="multipart").status_code, 400)


class PayloadTests(APITestCase):

    def test_live_payload_includes_attachments(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from .models import Message, MessageAttachment
        from .services import message_payload
        a = make_user("pl_a", "project_owner")
        b = make_user("pl_b", "project_owner")
        conv = make_conversation(a, b)
        msg = Message.objects.create(conversation=conv, sender=a, content="voir")
        MessageAttachment.objects.create(message=msg, file=SimpleUploadedFile("plan.pdf", b"x"), file_name="plan.pdf")
        payload = message_payload(msg)
        self.assertEqual(payload["attachments"][0]["file_name"], "plan.pdf")
        self.assertTrue(payload["attachments"][0]["file"].endswith(".pdf"))
