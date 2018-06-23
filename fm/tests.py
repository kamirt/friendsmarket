from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from fm.models import User

class UserTests(APITestCase):
    def test_create_user(self):
        """
        Ensure we can register a new user.
        """
        url = reverse('rest_register')
        data = {
            'email': 'skywalker@tatuin.net',
            'password1': 'notshortpassword',
            'password2': 'notshortpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().email, 'skywalker@tatuin.net')

    def test_view_profile(self):
        url = reverse('profile-view-update')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_fill_profile(self):
    	url = reverse('profile-view-update')
    	data = {
            'username': 'Luke Skywalker',
            'phone': '555-55-55',
            'birthdate': '01.01.3001',
            'gender': 'M',
            'enable_notif': True,
            'android_regid': '1234567890'
        }
    	response = self.client.put(url, data, format='json')
    	self.assertEqual(response.status_code, status.HTTP_200_OK)
    	self.assertEqual(User.objects.get().first_name, 'Luke')
    	self.assertEqual(User.objects.get().lase_name, 'Skywalker')
    	self.assertEqual(User.objects.get().phone, '555-55-55')
    	self.assertEqual(User.objects.get().birthdate, '01.01.3001')
    	self.assertEqual(User.objects.get().gender, 'M')
    	self.assertEqual(User.objects.get().enable_notif, True)
    	self.assertEqual(User.objects.get().ndroid_regid, '1234567890')
