from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from flight.models import Order, Ticket, Flight, Route, Airplane, Crew, Airport, AirplaneType
from flight.serializers import OrderSerializer, OrderRetrieveSerializer

User = get_user_model()


class OrderViewSetTests(APITestCase):

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

        self.order = Order.objects.create(user=self.user)
        self.ticket = Ticket.objects.create(row=1, seat=1, flight=self.flight, order=self.order)

    def test_list_orders_unauthorized(self):
        self.client.credentials()
        response = self.client.get(reverse("flight:orders-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_orders_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}")
        response = self.client.get(reverse("flight:orders-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        serializer = OrderSerializer([self.order], many=True)
        self.assertEqual(response.data['results'], serializer.data)

    def test_retrieve_order_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}")
        response = self.client.get(reverse("flight:orders-detail", kwargs={"pk": self.order.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order = Order.objects.prefetch_related(
            Prefetch('tickets',
                     queryset=Ticket.objects.select_related('flight__route__source', 'flight__route__destination'))
        ).get(id=self.order.id)
        serializer = OrderRetrieveSerializer(order)
        self.assertEqual(response.data, serializer.data)

    def test_create_order_with_tickets_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}")
        data = {
            "tickets": [
                {
                    "row": 2,
                    "seat": 3,
                    "flight": self.flight.id
                },
                {
                    "row": 3,
                    "seat": 4,
                    "flight": self.flight.id
                }
            ]
        }
        response = self.client.post(reverse("flight:orders-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 2)
        self.assertEqual(Order.objects.get(id=response.data["id"]).user, self.user)
        self.assertEqual(Ticket.objects.filter(order=response.data["id"]).count(), 2)

    def test_create_order_unauthorized(self):
        self.client.credentials()
        data = {}
        response = self.client.post(reverse("flight:orders-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_order_not_allowed(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}")
        data = {
            "tickets": [
                {
                    "row": 4,
                    "seat": 4,
                    "flight": self.flight.id
                }
            ]
        }
        response = self.client.put(reverse("flight:orders-detail", kwargs={"pk": self.order.pk}), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_partial_update_order_not_allowed(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}")
        data = {
            "tickets": [
                {
                    "row": 5,
                    "seat": 5,
                    "flight": self.flight.id
                }
            ]
        }
        response = self.client.patch(reverse("flight:orders-detail", kwargs={"pk": self.order.pk}), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_order_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token.access_token}")
        response = self.client.delete(reverse("flight:orders-detail", kwargs={"pk": self.order.pk}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Order.objects.count(), 0)

    def tearDown(self):
        self.client.credentials()
