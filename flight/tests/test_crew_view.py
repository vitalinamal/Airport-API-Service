from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from flight.models import Crew
from flight.serializers import CrewSerializer

User = get_user_model()


class CrewViewSetTests(APITestCase):

    def setUp(self):
        self.client = APIClient()

        self.crew1 = Crew.objects.create(first_name="John", last_name="Doe")
        self.crew2 = Crew.objects.create(first_name="Jane", last_name="Smith")

        self.user = User.objects.create_user(
            email="user@example.com", password="password", is_staff=False
        )
        self.user_token = RefreshToken.for_user(self.user)

        self.admin_user = User.objects.create_superuser(
            email="admin@example.com", password="password"
        )
        self.admin_token = RefreshToken.for_user(self.admin_user)

    def test_list_crew_unauthorized(self):
        self.client.credentials()
        response = self.client.get(reverse("flight:crew-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_crew_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}")
        response = self.client.get(reverse("flight:crew-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        serializer = CrewSerializer([self.crew1, self.crew2], many=True)
        self.assertEqual(response.data['results'], serializer.data)

    def test_retrieve_crew_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}")
        response = self.client.get(reverse("flight:crew-detail", kwargs={"pk": self.crew1.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = CrewSerializer(self.crew1)
        self.assertEqual(response.data, serializer.data)

    def test_create_crew_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token.access_token}")
        data = {
            "first_name": "New",
            "last_name": "Crew",
        }
        response = self.client.post(reverse("flight:crew-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Crew.objects.count(), 3)
        self.assertEqual(Crew.objects.get(id=response.data["id"]).first_name, "New")
        self.assertEqual(Crew.objects.get(id=response.data["id"]).last_name, "Crew")

    def test_create_crew_non_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}")
        data = {
            "first_name": "New",
            "last_name": "Crew",
        }
        response = self.client.post(reverse("flight:crew-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_crew_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token.access_token}")
        data = {
            "first_name": "Updated",
            "last_name": "Crew",
        }
        response = self.client.put(reverse("flight:crew-detail", kwargs={"pk": self.crew1.pk}), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.crew1.refresh_from_db()
        self.assertEqual(self.crew1.first_name, "Updated")
        self.assertEqual(self.crew1.last_name, "Crew")

    def test_update_crew_non_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}")
        data = {
            "first_name": "Updated",
            "last_name": "Crew",
        }
        response = self.client.put(reverse("flight:crew-detail", kwargs={"pk": self.crew1.pk}), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_crew_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token.access_token}")
        response = self.client.delete(reverse("flight:crew-detail", kwargs={"pk": self.crew1.pk}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Crew.objects.count(), 1)

    def test_delete_crew_non_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}")
        response = self.client.delete(reverse("flight:crew-detail", kwargs={"pk": self.crew1.pk}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def tearDown(self):
        self.client.credentials()
