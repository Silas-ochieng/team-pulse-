from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

class CustomUserTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123',
            user_type='staff',
            phone_number='1234567890'
        )
        self.community_user = User.objects.create_user(
            username='communityuser',
            email='community@example.com',
            password='testpass123',
            user_type='community',
            phone_number='0987654321'
        )

    def test_create_user(self):
        """Test creating a new user"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='community'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.user_type, 'community')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        """Test creating a new superuser"""
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='testpass123'
        )
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_staff)

    def test_user_type_choices(self):
        """Test user type choices are enforced"""
        self.assertEqual(self.staff_user.user_type, 'staff')
        self.assertEqual(self.community_user.user_type, 'community')

    def test_staff_user_permissions(self):
        """Test staff user has correct permissions"""
        self.assertTrue(self.staff_user.is_staff_user())
        self.assertFalse(self.community_user.is_staff_user())

    def test_str_representation(self):
        """Test string representation of user"""
        self.assertEqual(str(self.staff_user), self.staff_user.username)