from datetime import datetime

from django.db.models import F, Count, Prefetch
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from flight.models import Crew, Route, AirplaneType, Airplane, Flight, Order, Airport, Ticket
from flight.serializers import (
    CrewSerializer,
    AirportSerializer,
    AirportRetrieveSerializer,
    RouteSerializer,
    RouteListSerializer,
    RouteRetrieveSerializer,
    AirplaneTypeSerializer,
    AirplaneSerializer,
    AirplaneListSerializer,
    AirplaneRetrieveSerializer,
    AirplaneImageSerializer,
    FlightSerializer,
    FlightListSerializer,
    FlightRetrieveSerializer,
    OrderSerializer,
    OrderRetrieveSerializer,
)


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer

    def get_queryset(self):
        if self.action == 'retrieve':
            return self.queryset.prefetch_related(
                Prefetch('routes_from', queryset=Route.objects.select_related('source', 'destination')),
                Prefetch('routes_to', queryset=Route.objects.select_related('source', 'destination'))
            )
        return self.queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AirportRetrieveSerializer
        return self.serializer_class


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer

    def get_queryset(self):
        if self.action in ["list", 'retrieve']:
            return self.queryset.select_related("source", "destination")
        return self.queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return RouteListSerializer
        if self.action == 'retrieve':
            return RouteRetrieveSerializer
        return self.serializer_class


class AirplaneTypeViewSet(viewsets.ModelViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.all()
    serializer_class = AirplaneSerializer

    def get_queryset(self):
        if self.action in ["list", 'retrieve']:
            return self.queryset.select_related("airplane_type")
        return self.queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return AirplaneListSerializer
        elif self.action == 'retrieve':
            return AirplaneRetrieveSerializer
        elif self.action == 'upload_image':
            return AirplaneImageSerializer
        return self.serializer_class

    @action(
        methods=("POST",),
        detail=True,
        url_path="upload-image",
    )
    def upload_image(self, request, pk=None):
        airplane = self.get_object()
        serializer = self.get_serializer(airplane, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.all()
    serializer_class = FlightSerializer

    @staticmethod
    def _params_to_list(qs):
        """Converts a string to a list of parameters"""
        return qs.split("-")

    def get_queryset(self):
        queryset = self.queryset
        route = self.request.query_params.get("route")
        airport = self.request.query_params.get("airport")
        date = self.request.query_params.get("date")

        if route:
            route_list = self._params_to_list(route)
            queryset = queryset.filter(route__source__closest_big_city__iexact=route_list[0],
                                       route__destination__closest_big_city__iexact=route_list[1])

        if airport:
            queryset = queryset.filter(route__source__closest_big_city__iexact=airport)

        if date:
            date = datetime.strptime(date, "%Y-%m-%d").date()
            queryset = queryset.filter(departure_time__date=date)

        if self.action in ["list", "retrieve"]:
            queryset = queryset.select_related("airplane", "route__source", "route__destination").prefetch_related(
                "crew").annotate(
                tickets_available=(
                        F("airplane__rows") * F("airplane__seats_in_row") - Count("tickets")
                )
            )

        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return FlightListSerializer
        if self.action == 'retrieve':
            return FlightRetrieveSerializer
        return self.serializer_class


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_queryset(self):
        ticket_prefetch = Prefetch('tickets', queryset=Ticket.objects.select_related('flight__route__source',
                                                                                     'flight__route__destination'))
        return self.queryset.filter(user=self.request.user).prefetch_related(ticket_prefetch)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return OrderRetrieveSerializer

        return OrderSerializer
