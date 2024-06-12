import tempfile
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from PIL import Image

from flight.models import Airplane, AirplaneType
from flight.serializers import AirplaneListSerializer, AirplaneRetrieveSerializer

User = get_user_model()


class AirplaneViewSetTests(APITestCase):

    def setUp(self):
        self.client = APIClient()

        self.airplane_type1 = AirplaneType.objects.create(name="Type1")
        self.airplane_type2 = AirplaneType.objects.create(name="Type2")

        self.airplane1 = Airplane.objects.create(
            name="Airplane1", rows=10, seats_in_row=4, airplane_type=self.airplane_type1
        )
        self.airplane2 = Airplane.objects.create(
            name="Airplane2", rows=12, seats_in_row=5, airplane_type=self.airplane_type2
        )

        self.user = User.objects.create_user(
            email="user@example.com", password="password", is_staff=False
        )
        self.user_token = RefreshToken.for_user(self.user)

        self.admin_user = User.objects.create_superuser(
            email="admin@example.com", password="password"
        )
        self.admin_token = RefreshToken.for_user(self.admin_user)

    def test_list_airplanes_unauthorized(self):
        self.client.credentials()
        response = self.client.get(reverse("flight:airplanes-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_airplanes_authenticated(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}"
        )
        response = self.client.get(reverse("flight:airplanes-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        serializer = AirplaneListSerializer([self.airplane1, self.airplane2], many=True)
        self.assertEqual(response.data["results"], serializer.data)

    def test_retrieve_airplane_authenticated(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}"
        )
        response = self.client.get(
            reverse("flight:airplanes-detail", kwargs={"pk": self.airplane1.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        airplane = Airplane.objects.select_related("airplane_type").get(
            id=self.airplane1.id
        )
        serializer = AirplaneRetrieveSerializer(airplane)
        self.assertEqual(response.data, serializer.data)

    def test_create_airplane_admin(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token.access_token}"
        )
        data = {
            "name": "Airplane3",
            "rows": 14,
            "seats_in_row": 6,
            "airplane_type": self.airplane_type1.id,
        }
        response = self.client.post(
            reverse("flight:airplanes-list"), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Airplane.objects.count(), 3)
        self.assertEqual(Airplane.objects.get(id=response.data["id"]).name, "Airplane3")

    def test_create_airplane_non_admin(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}"
        )
        data = {
            "name": "Airplane3",
            "rows": 14,
            "seats_in_row": 6,
            "airplane_type": self.airplane_type1.id,
        }
        response = self.client.post(
            reverse("flight:airplanes-list"), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_airplane_admin(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token.access_token}"
        )
        data = {
            "name": "Updated Airplane",
            "rows": 10,
            "seats_in_row": 4,
            "airplane_type": self.airplane_type1.id,
        }
        response = self.client.put(
            reverse("flight:airplanes-detail", kwargs={"pk": self.airplane1.pk}), data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.airplane1.refresh_from_db()
        self.assertEqual(self.airplane1.name, "Updated Airplane")

    def test_update_airplane_non_admin(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}"
        )
        data = {
            "name": "Updated Airplane",
            "rows": 10,
            "seats_in_row": 4,
            "airplane_type": self.airplane_type1.id,
        }
        response = self.client.put(
            reverse("flight:airplanes-detail", kwargs={"pk": self.airplane1.pk}), data
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_partial_update_airplane_admin(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token.access_token}"
        )
        data = {"name": "Partially Updated Airplane"}
        response = self.client.patch(
            reverse("flight:airplanes-detail", kwargs={"pk": self.airplane1.pk}), data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.airplane1.refresh_from_db()
        self.assertEqual(self.airplane1.name, "Partially Updated Airplane")

    def test_partial_update_airplane_non_admin(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}"
        )
        data = {"name": "Partially Updated Airplane"}
        response = self.client.patch(
            reverse("flight:airplanes-detail", kwargs={"pk": self.airplane1.pk}), data
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_airplane_admin(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token.access_token}"
        )
        response = self.client.delete(
            reverse("flight:airplanes-detail", kwargs={"pk": self.airplane1.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Airplane.objects.count(), 1)

    def test_delete_airplane_non_admin(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}"
        )
        response = self.client.delete(
            reverse("flight:airplanes-detail", kwargs={"pk": self.airplane1.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_upload_image_admin(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token.access_token}"
        )
        url = reverse("flight:airplanes-upload-image", kwargs={"pk": self.airplane1.pk})
        with tempfile.NamedTemporaryFile(suffix=".jpg") as temp_image:
            image = Image.new("RGB", (100, 100))
            image.save(temp_image, format="JPEG")
            temp_image.seek(0)
            response = self.client.post(url, {"image": temp_image}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.airplane1.refresh_from_db()
        self.assertTrue(self.airplane1.image)

    def test_upload_image_non_admin(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}"
        )
        url = reverse("flight:airplanes-upload-image", kwargs={"pk": self.airplane1.pk})
        with tempfile.NamedTemporaryFile(suffix=".jpg") as temp_image:
            image = Image.new("RGB", (100, 100))
            image.save(temp_image, format="JPEG")
            temp_image.seek(0)
            response = self.client.post(url, {"image": temp_image}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def tearDown(self):
        self.client.credentials()
