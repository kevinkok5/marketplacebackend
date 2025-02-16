from django.test import TestCase

from django.contrib.auth import get_user_model

class UserModelTest(TestCase):
    def setUp(self):
        self.User = get_user_model()

    def test_create_user_with_valid_data(self):
        user = self.User.objects.create_user(
            first_name="John",
            username="john123",
            email="john@example.com",
            password="password123",
        )
        self.assertEqual(user.username, "john123")
        self.assertTrue(user.check_password("password123"))

    def test_auto_generate_username(self):
        user = self.User.objects.create_user(
            first_name="Jane",
            email="jane@example.com",
            password="password123",
        )
        self.assertTrue(user.username.startswith("jane"))

    def test_create_superuser(self):
        superuser = self.User.objects.create_superuser(
            first_name="Admin",
            username="admin",
            email="admin@example.com",
            password="adminpassword",
        )
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
