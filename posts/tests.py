from django.core.cache import cache
from rest_framework.test import APITestCase

from booking.tests import make_user


class PostFlowTests(APITestCase):

    def setUp(self):
        cache.clear()
        self.awa = make_user("awa", "project_owner")
        self.awa.first_name, self.awa.last_name = "Awa", "Traoré"
        self.awa.save()
        self.ibra = make_user("ibra", "project_owner")
        self.client.force_authenticate(self.awa)

    def _create(self, content="Nous levons des fonds #objectif_financement #stade_prototype"):
        return self.client.post("/api/posts/", {"content": content}, format="json")

    def test_create_post_returns_hashtag_names_and_full_author_name(self):
        r = self._create()
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(sorted(r.data["hashtags"]), ["objectif_financement", "stade_prototype"])
        self.assertEqual(r.data["author_name"], "Awa Traoré")

        feed = self.client.get("/api/posts/")
        self.assertEqual(feed.data["results"][0]["hashtags"][0].__class__, str)

    def test_like_toggle_comment_share(self):
        post_id = self._create().data["id"]

        self.client.force_authenticate(self.ibra)
        self.assertEqual(self.client.post(f"/api/posts/{post_id}/like/").status_code, 200)
        self.assertEqual(self.client.get(f"/api/posts/{post_id}/").data["likes_count"], 1)
        self.assertTrue(self.client.get(f"/api/posts/{post_id}/").data["liked_by_me"])
        self.client.post(f"/api/posts/{post_id}/like/")  # retire le like
        self.assertEqual(self.client.get(f"/api/posts/{post_id}/").data["likes_count"], 0)

        r = self.client.post(f"/api/posts/{post_id}/comment/", {"content": "Bravo !"}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        comments = self.client.get(f"/api/posts/{post_id}/comments/")
        self.assertEqual(comments.data["results"][0]["content"], "Bravo !")
        self.assertEqual(self.client.get(f"/api/posts/{post_id}/").data["comments_count"], 1)

        r = self.client.post(f"/api/posts/{post_id}/share/", {"comment": "À lire"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.client.get(f"/api/posts/{post_id}/").data["shares_count"], 1)

    def test_only_author_can_delete(self):
        post_id = self._create().data["id"]
        self.client.force_authenticate(self.ibra)
        self.assertIn(self.client.delete(f"/api/posts/{post_id}/manage/").status_code, (403, 404))
        self.client.force_authenticate(self.awa)
        self.assertEqual(self.client.delete(f"/api/posts/{post_id}/manage/").status_code, 204)

    def test_anonymous_cannot_publish(self):
        self.client.force_authenticate(None)
        self.assertEqual(self._create().status_code, 401)


from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image


def png(name="photo.png", size=(8, 8)):
    buf = BytesIO()
    Image.new("RGB", size, (60, 40, 80)).save(buf, "PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


class PostImageTests(APITestCase):

    def setUp(self):
        cache.clear()
        self.user = make_user("photo", "project_owner")
        self.client.force_authenticate(self.user)

    def test_post_with_several_images(self):
        r = self.client.post(
            "/api/posts/",
            {"content": "Voir nos photos #objectif_actualite", "images": [png("a.png"), png("b.png")]},
            format="multipart",
        )
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(len(r.data["images"]), 2)
        self.assertTrue(r.data["images"][0]["image"].startswith("http"))

    def test_rejects_non_image_too_many_and_empty_files(self):
        fake = SimpleUploadedFile("x.png", b"pas une image", content_type="image/png")
        r = self.client.post("/api/posts/", {"content": "x", "images": [fake]}, format="multipart")
        self.assertEqual(r.status_code, 400)

        many = [png(f"{i}.png") for i in range(6)]
        r = self.client.post("/api/posts/", {"content": "x", "images": many}, format="multipart")
        self.assertEqual(r.status_code, 400)

        from posts.models import Post
        self.assertEqual(Post.objects.count(), 0)  # rien n'a été créé

    def test_project_cover_image(self):
        r = self.client.post(
            "/api/projects/",
            {"title": "AgriPlus", "description": "d", "sector": "Agriculture", "country": "BF",
             "budget": "1000", "stage": "idea", "cover_image": png("cover.png")},
            format="multipart",
        )
        self.assertEqual(r.status_code, 201, r.data)
        self.assertTrue(r.data["cover_image"])


class PostProjectLinkTests(APITestCase):

    def setUp(self):
        cache.clear()
        from projects.models import Project
        self.owner = make_user("p_owner", "project_owner")
        self.owner.first_name, self.owner.last_name = "Awa", "Traoré"
        self.owner.save()
        self.owner.profile.headline = "Fondatrice · Kër Care"
        self.owner.profile.city = "Abidjan"
        self.owner.profile.save()
        self.project = Project.objects.create(owner=self.owner, title="Kër Care", description="d", sector="Santé", country="CI", budget=1, stage="prototype")
        self.other = make_user("p_other", "project_owner")

    def test_post_linked_to_own_project(self):
        self.client.force_authenticate(self.owner)
        r = self.client.post("/api/posts/", {"title": "Premier centre pilote", "content": "Annonce", "project": self.project.id}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["project"], self.project.id)
        self.assertEqual(r.data["project_title"], "Kër Care")
        self.assertEqual(r.data["title"], "Premier centre pilote")
        self.assertEqual(r.data["author_headline"], "Fondatrice · Kër Care · Abidjan")

    def test_cannot_link_someone_elses_project(self):
        self.client.force_authenticate(self.other)
        r = self.client.post("/api/posts/", {"content": "x", "project": self.project.id}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_project_needs(self):
        self.client.force_authenticate(self.owner)
        r = self.client.post(f"/api/projects/{self.project.id}/needs/", {"kind": "expertise", "title": "Expert IoT", "detail": "Mission · 3 mois"}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        detail = self.client.get(f"/api/projects/{self.project.id}/")
        self.assertEqual(detail.data["needs"][0]["title"], "Expert IoT")
        self.assertEqual(detail.data["owner_headline"], "Fondatrice · Kër Care")

        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.post(f"/api/projects/{self.project.id}/needs/", {"title": "X"}, format="json").status_code, 403)
        self.assertEqual(self.client.delete(f"/api/projects/needs/{r.data['id']}/").status_code, 404)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.delete(f"/api/projects/needs/{r.data['id']}/").status_code, 204)
