from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from flight.models import Airport, Route
from flight.serializers import AirportSerializer, AirportRetrieveSerializer

User = get_user_model()


class AirportViewSetTests(APITestCase):

    def setUp(self):
        self.client = APIClient()

        self.airport1 = Airport.objects.create(name="Airport1", closest_big_city="City1")
        self.airport2 = Airport.objects.create(name="Airport2", closest_big_city="City2")

        self.route1 = Route.objects.create(source=self.airport1, destination=self.airport2, distance=120)
        self.route2 = Route.objects.create(source=self.airport2, destination=self.airport1, distance=130)

        self.user = User.objects.create_user(
            email="user@example.com", password="password", is_staff=False
        )
        self.user_token = RefreshToken.for_user(self.user)

        self.admin_user = User.objects.create_superuser(
            email="admin@example.com", password="password"
        )
        self.admin_token = RefreshToken.for_user(self.admin_user)

    def test_list_airports_unauthorized(self):
        self.client.credentials()
        response = self.client.get(reverse("flight:airports-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_airports_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}")
        response = self.client.get(reverse("flight:airports-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        serializer = AirportSerializer([self.airport1, self.airport2], many=True)
        self.assertEqual(response.data['results'], serializer.data)

    def test_retrieve_airport_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}")
        response = self.client.get(reverse("flight:airports-detail", kwargs={"pk": self.airport1.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        airport = Airport.objects.prefetch_related(
            Prefetch('routes_from', queryset=Route.objects.select_related('source', 'destination')),
            Prefetch('routes_to', queryset=Route.objects.select_related('source', 'destination'))
        ).get(id=self.airport1.id)
        serializer = AirportRetrieveSerializer(airport)
        self.assertEqual(response.data, serializer.data)

    def test_create_airport_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token.access_token}")
        data = {
            "name": "Airport3",
            "closest_big_city": "City3",
        }
        response = self.client.post(reverse("flight:airports-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Airport.objects.count(), 3)
        self.assertEqual(Airport.objects.get(id=response.data["id"]).name, "Airport3")

    def test_create_airport_non_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}")
        data = {
            "name": "Airport3",
            "closest_big_city": "City3",
        }
        response = self.client.post(reverse("flight:airports-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_airport_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token.access_token}")
        data = {
            "name": "Updated Airport",
            "closest_big_city": "Updated City",
        }
        response = self.client.put(reverse("flight:airports-detail", kwargs={"pk": self.airport1.pk}), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.airport1.refresh_from_db()
        self.assertEqual(self.airport1.name, "Updated Airport")
        self.assertEqual(self.airport1.closest_big_city, "Updated City")

    def test_update_airport_non_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}")
        data = {
            "name": "Updated Airport",
            "closest_big_city": "Updated City",
        }
        response = self.client.put(reverse("flight:airports-detail", kwargs={"pk": self.airport1.pk}), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_partial_update_airport_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token.access_token}")
        data = {
            "name": "Partially Updated Airport"
        }
        response = self.client.patch(reverse("flight:airports-detail", kwargs={"pk": self.airport1.pk}), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.airport1.refresh_from_db()
        self.assertEqual(self.airport1.name, "Partially Updated Airport")

    def test_partial_update_airport_non_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}")
        data = {
            "name": "Partially Updated Airport"
        }
        response = self.client.patch(reverse("flight:airports-detail", kwargs={"pk": self.airport1.pk}), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_airport_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token.access_token}")
        response = self.client.delete(reverse("flight:airports-detail", kwargs={"pk": self.airport1.pk}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Airport.objects.count(), 1)

    def test_delete_airport_non_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}")
        response = self.client.delete(reverse("flight:airports-detail", kwargs={"pk": self.airport1.pk}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def tearDown(self):
        self.client.credentials()
