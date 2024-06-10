from django.contrib.auth import get_user_model
from django.db.models import Count, F
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from flight.models import Flight, Route, Airplane, Crew, Airport, AirplaneType
from flight.serializers import FlightListSerializer, FlightRetrieveSerializer

User = get_user_model()


class FlightViewSetTests(APITestCase):

    def setUp(self):
        self.client = APIClient()

        self.airport1 = Airport.objects.create(name="Airport1", closest_big_city="City1")
        self.airport2 = Airport.objects.create(name="Airport2", closest_big_city="City2")

        self.route = Route.objects.create(source=self.airport1, destination=self.airport2, distance=100)

        self.airplane_type = AirplaneType.objects.create(name="Type1")
        self.airplane = Airplane.objects.create(name="Airplane1", rows=10, seats_in_row=4,
                                                airplane_type=self.airplane_type)

        self.crew1 = Crew.objects.create(first_name="John", last_name="Doe")
        self.crew2 = Crew.objects.create(first_name="Jane", last_name="Smith")

        self.flight = Flight.objects.create(
            route=self.route,
            airplane=self.airplane,
            departure_time="2023-01-01T10:00:00Z",
            arrival_time="2023-01-01T12:00:00Z"
        )
        self.flight.crew.set([self.crew1, self.crew2])

        self.user = User.objects.create_user(
            email="user@example.com", password="password", is_staff=False
        )
        self.user_token = RefreshToken.for_user(self.user)

        self.admin_user = User.objects.create_superuser(
            email="admin@example.com", password="password"
        )
        self.admin_token = RefreshToken.for_user(self.admin_user)

    def test_list_flights_unauthorized(self):
        self.client.credentials()
        response = self.client.get(reverse("flight:flights-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_flights_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}")
        response = self.client.get(reverse("flight:flights-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        flight = Flight.objects.select_related("airplane", "route__source", "route__destination").prefetch_related(
            "crew").annotate(
            tickets_available=(
                    F("airplane__rows") * F("airplane__seats_in_row") - Count("tickets")
            )
        ).get(id=self.flight.id)

        serializer = FlightListSerializer([flight], many=True)
        self.assertEqual(response.data['results'], serializer.data)

    def test_retrieve_flight_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}")
        response = self.client.get(reverse("flight:flights-detail", kwargs={"pk": self.flight.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        flight = Flight.objects.select_related("airplane", "route__source", "route__destination").prefetch_related(
            "crew").get(id=self.flight.id)
        serializer = FlightRetrieveSerializer(flight)
        self.assertEqual(response.data, serializer.data)

    def test_create_flight_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token.access_token}")
        data = {
            "route": self.route.id,
            "airplane": self.airplane.id,
            "crew": [self.crew1.id, self.crew2.id],
            "departure_time": "2023-01-01T14:00:00Z",
            "arrival_time": "2023-01-01T16:00:00Z"
        }
        response = self.client.post(reverse("flight:flights-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Flight.objects.count(), 2)
        self.assertEqual(Flight.objects.get(id=response.data["id"]).route, self.route)

    def test_create_flight_non_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}")
        data = {
            "route": self.route.id,
            "airplane": self.airplane.id,
            "crew": [self.crew1.id, self.crew2.id],
            "departure_time": "2023-01-01T14:00:00Z",
            "arrival_time": "2023-01-01T16:00:00Z"
        }
        response = self.client.post(reverse("flight:flights-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_flight_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token.access_token}")
        data = {
            "route": self.route.id,
            "airplane": self.airplane.id,
            "crew": [self.crew1.id, self.crew2.id],
            "departure_time": "2023-01-01T15:00:00Z",
            "arrival_time": "2023-01-01T17:00:00Z"
        }
        response = self.client.put(reverse("flight:flights-detail", kwargs={"pk": self.flight.pk}), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.flight.refresh_from_db()
        self.assertEqual(self.flight.departure_time.isoformat(), "2023-01-01T15:00:00+00:00")
        self.assertEqual(self.flight.arrival_time.isoformat(), "2023-01-01T17:00:00+00:00")

    def test_update_flight_non_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}")
        data = {
            "route": self.route.id,
            "airplane": self.airplane.id,
            "crew": [self.crew1.id, self.crew2.id],
            "departure_time": "2023-01-01T15:00:00Z",
            "arrival_time": "2023-01-01T17:00:00Z"
        }
        response = self.client.put(reverse("flight:flights-detail", kwargs={"pk": self.flight.pk}), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_partial_update_flight_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token.access_token}")
        data = {
            "departure_time": "2023-01-01T16:00:00Z"
        }
        response = self.client.patch(reverse("flight:flights-detail", kwargs={"pk": self.flight.pk}), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.flight.refresh_from_db()
        self.assertEqual(self.flight.departure_time.isoformat(), "2023-01-01T16:00:00+00:00")

    def test_partial_update_flight_non_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}")
        data = {
            "departure_time": "2023-01-01T16:00:00Z"
        }
        response = self.client.patch(reverse("flight:flights-detail", kwargs={"pk": self.flight.pk}), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_flight_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token.access_token}")
        response = self.client.delete(reverse("flight:flights-detail", kwargs={"pk": self.flight.pk}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Flight.objects.count(), 0)

    def test_delete_flight_non_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}")
        response = self.client.delete(reverse("flight:flights-detail", kwargs={"pk": self.flight.pk}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def tearDown(self):
        self.client.credentials()
