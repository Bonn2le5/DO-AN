from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from accounts.serializers import NguoiDungSerializer

NguoiDung = get_user_model()


class AuthProfileTestCase(TestCase):
    def setUp(self):
        self.user = NguoiDung.objects.create_user(
            username="khach_test_profile",
            email="profile_test@moc.vn",
            thu_dien_tu="profile_test@moc.vn",
            first_name="Văn",
            last_name="Vũ",
            password="Password@123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_nguoi_dung_serializer(self):
        serializer = NguoiDungSerializer(self.user)
        data = serializer.data
        self.assertEqual(data["email"], "profile_test@moc.vn")
        self.assertEqual(data["name"], "Văn Vũ")
        self.assertEqual(data["username"], "khach_test_profile")

    def test_api_auth_profile_endpoint(self):
        response = self.client.get("/api/auth/profile/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "profile_test@moc.vn")
        self.assertEqual(response.data["name"], "Văn Vũ")

