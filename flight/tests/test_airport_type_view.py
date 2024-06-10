from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from flight.models import AirplaneType
from flight.serializers import AirplaneTypeSerializer

User = get_user_model()


class AirplaneTypeViewSetTests(APITestCase):

    def setUp(self):
        self.client = APIClient()

        self.airplane_type1 = AirplaneType.objects.create(name="Type1")
        self.airplane_type2 = AirplaneType.objects.create(name="Type2")

        self.user = User.objects.create_user(
            email="user@example.com", password="password", is_staff=False
        )
        self.user_token = RefreshToken.for_user(self.user)

        self.admin_user = User.objects.create_superuser(
            email="admin@example.com", password="password"
        )
        self.admin_token = RefreshToken.for_user(self.admin_user)

    def test_list_airplane_types_unauthorized(self):
        self.client.credentials()
        response = self.client.get(reverse("flight:airplane-types-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_airplane_types_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}")
        response = self.client.get(reverse("flight:airplane-types-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        serializer = AirplaneTypeSerializer([self.airplane_type1, self.airplane_type2], many=True)
        self.assertEqual(response.data['results'], serializer.data)

    def test_retrieve_airplane_type_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}")
        response = self.client.get(reverse("flight:airplane-types-detail", kwargs={"pk": self.airplane_type1.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = AirplaneTypeSerializer(self.airplane_type1)
        self.assertEqual(response.data, serializer.data)

    def test_create_airplane_type_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token.access_token}")
        data = {
            "name": "Type3",
        }
        response = self.client.post(reverse("flight:airplane-types-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AirplaneType.objects.count(), 3)
        self.assertEqual(AirplaneType.objects.get(id=response.data["id"]).name, "Type3")

    def test_create_airplane_type_non_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}")
        data = {
            "name": "Type3",
        }
        response = self.client.post(reverse("flight:airplane-types-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_airplane_type_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token.access_token}")
        data = {
            "name": "Updated Type",
        }
        response = self.client.put(reverse("flight:airplane-types-detail", kwargs={"pk": self.airplane_type1.pk}), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.airplane_type1.refresh_from_db()
        self.assertEqual(self.airplane_type1.name, "Updated Type")

    def test_update_airplane_type_non_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}")
        data = {
            "name": "Updated Type",
        }
        response = self.client.put(reverse("flight:airplane-types-detail", kwargs={"pk": self.airplane_type1.pk}), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_partial_update_airplane_type_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token.access_token}")
        data = {
            "name": "Partially Updated Type"
        }
        response = self.client.patch(reverse("flight:airplane-types-detail", kwargs={"pk": self.airplane_type1.pk}), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.airplane_type1.refresh_from_db()
        self.assertEqual(self.airplane_type1.name, "Partially Updated Type")

    def test_partial_update_airplane_type_non_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}")
        data = {
            "name": "Partially Updated Type"
        }
        response = self.client.patch(reverse("flight:airplane-types-detail", kwargs={"pk": self.airplane_type1.pk}), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_airplane_type_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token.access_token}")
        response = self.client.delete(reverse("flight:airplane-types-detail", kwargs={"pk": self.airplane_type1.pk}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(AirplaneType.objects.count(), 1)

    def test_delete_airplane_type_non_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}")
        response = self.client.delete(reverse("flight:airplane-types-detail", kwargs={"pk": self.airplane_type1.pk}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def tearDown(self):
        self.client.credentials()
