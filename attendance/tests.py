from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from users.models import CustomUser
from .models import Attendance

class AttendanceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123',
            user_type='community'
        )
        self.client.force_authenticate(user=self.user)

    def test_check_in(self):
        response = self.client.post(reverse('check-in'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Attendance.objects.filter(user=self.user).exists())

    def test_check_out(self):
        # Create check-in first
        attendance = Attendance.objects.create(user=self.user)
        response = self.client.post(reverse('check-out'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        attendance.refresh_from_db()
        self.assertIsNotNone(attendance.check_out)