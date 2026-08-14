from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.test import APITestCase


class AuthAPITests(APITestCase):
    credentials = {"username": "diego", "password": "Str0ngPass!23"}

    def setUp(self):
        # Throttle counters live in the cache and would leak between tests.
        cache.clear()

    def test_register_creates_user_with_hashed_password(self):
        response = self.client.post("/api/auth/register/", self.credentials)
        self.assertEqual(response.status_code, 201)
        self.assertNotIn("password", response.data)
        user = User.objects.get(username="diego")
        self.assertTrue(user.check_password(self.credentials["password"]))

    def test_register_rejects_weak_password(self):
        response = self.client.post(
            "/api/auth/register/", {"username": "diego", "password": "123"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("password", response.data)

    def test_register_rejects_duplicate_username(self):
        User.objects.create_user(**self.credentials)
        response = self.client.post("/api/auth/register/", self.credentials)
        self.assertEqual(response.status_code, 400)

    def test_login_sets_http_only_cookies_and_authenticates_requests(self):
        User.objects.create_user(**self.credentials)
        response = self.client.post("/api/auth/login/", self.credentials)
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.cookies)
        self.assertIn("refresh", response.cookies)
        self.assertTrue(response.cookies["access"]["httponly"])
        self.assertTrue(response.cookies["refresh"]["httponly"])
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)
        self.client.cookies["access"] = response.cookies["access"].value
        self.assertEqual(self.client.get("/api/organizations/").status_code, 200)

    def test_login_rejects_wrong_password(self):
        User.objects.create_user(**self.credentials)
        response = self.client.post(
            "/api/auth/login/", {"username": "diego", "password": "wrong"}
        )
        self.assertEqual(response.status_code, 401)

    def test_login_is_throttled(self):
        User.objects.create_user(**self.credentials)
        attempt = {"username": "diego", "password": "wrong"}
        for _ in range(10):
            self.client.post("/api/auth/login/", attempt)
        response = self.client.post("/api/auth/login/", attempt)
        self.assertEqual(response.status_code, 429)
