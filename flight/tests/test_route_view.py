from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from flight.models import Airport, Route
from flight.serializers import RouteListSerializer, RouteRetrieveSerializer

User = get_user_model()


class RouteViewSetTests(APITestCase):

    def setUp(self):
        self.client = APIClient()

        self.airport1 = Airport.objects.create(
            name="Airport1", closest_big_city="City1"
        )
        self.airport2 = Airport.objects.create(
            name="Airport2", closest_big_city="City2"
        )
        self.airport3 = Airport.objects.create(
            name="Airport3", closest_big_city="City3"
        )

        self.route1 = Route.objects.create(
            source=self.airport1, destination=self.airport2, distance=100
        )
        self.route2 = Route.objects.create(
            source=self.airport2, destination=self.airport3, distance=200
        )

        self.user = User.objects.create_user(
            email="user@example.com", password="password", is_staff=False
        )
        self.user_token = RefreshToken.for_user(self.user)

        self.admin_user = User.objects.create_superuser(
            email="admin@example.com", password="password"
        )
        self.admin_token = RefreshToken.for_user(self.admin_user)

    def test_list_routes_unauthorized(self):
        self.client.credentials()
        response = self.client.get(reverse("flight:routs-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_routes_authenticated(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}"
        )
        response = self.client.get(reverse("flight:routs-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        serializer = RouteListSerializer([self.route1, self.route2], many=True)
        self.assertEqual(response.data["results"], serializer.data)

    def test_retrieve_route_authenticated(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}"
        )
        response = self.client.get(
            reverse("flight:routs-detail", kwargs={"pk": self.route1.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        route = Route.objects.select_related("source", "destination").get(
            id=self.route1.id
        )
        serializer = RouteRetrieveSerializer(route)
        self.assertEqual(response.data, serializer.data)

    def test_create_route_admin(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token.access_token}"
        )
        data = {
            "source": self.airport1.id,
            "destination": self.airport3.id,
            "distance": 300,
        }
        response = self.client.post(reverse("flight:routs-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Route.objects.count(), 3)
        self.assertEqual(Route.objects.get(id=response.data["id"]).distance, 300)

    def test_create_route_non_admin(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}"
        )
        data = {
            "source": self.airport1.id,
            "destination": self.airport3.id,
            "distance": 300,
        }
        response = self.client.post(reverse("flight:routs-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_route_admin(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token.access_token}"
        )
        data = {
            "source": self.airport1.id,
            "destination": self.airport3.id,
            "distance": 150,
        }
        response = self.client.put(
            reverse("flight:routs-detail", kwargs={"pk": self.route1.pk}), data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.route1.refresh_from_db()
        self.assertEqual(self.route1.distance, 150)

    def test_update_route_non_admin(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}"
        )
        data = {
            "source": self.airport1.id,
            "destination": self.airport3.id,
            "distance": 150,
        }
        response = self.client.put(
            reverse("flight:routs-detail", kwargs={"pk": self.route1.pk}), data
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_partial_update_route_admin(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token.access_token}"
        )
        data = {"distance": 175}
        response = self.client.patch(
            reverse("flight:routs-detail", kwargs={"pk": self.route1.pk}), data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.route1.refresh_from_db()
        self.assertEqual(self.route1.distance, 175)

    def test_partial_update_route_non_admin(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}"
        )
        data = {"distance": 175}
        response = self.client.patch(
            reverse("flight:routs-detail", kwargs={"pk": self.route1.pk}), data
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_route_admin(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.admin_token.access_token}"
        )
        response = self.client.delete(
            reverse("flight:routs-detail", kwargs={"pk": self.route1.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Route.objects.count(), 1)

    def test_delete_route_non_admin(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}"
        )
        response = self.client.delete(
            reverse("flight:routs-detail", kwargs={"pk": self.route1.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def tearDown(self):
        self.client.credentials()
