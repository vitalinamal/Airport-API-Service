from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from flight.models import (
    Crew,
    Airport,
    Route,
    AirplaneType,
    Airplane,
    Flight,
    Order,
    Ticket,
)


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ["id", "first_name", "last_name", "full_name"]


class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ["id", "name", "closest_big_city"]


class AirportRetrieveSerializer(AirportSerializer):
    routes = serializers.SerializerMethodField()

    class Meta:
        model = Airport
        fields = AirportSerializer.Meta.fields + ["routes"]

    def get_routes(self, obj):
        routes_from = obj.routes_from.all()

        routes = []

        for route in routes_from:
            routes.append(
                {
                    "source": route.source.name,
                    "destination": route.destination.name,
                    "distance": route.distance,
                    "cities_route": route.cities_route,
                }
            )

        return routes


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ["id", "source", "destination", "distance"]


class RouteListSerializer(RouteSerializer):
    source = serializers.SlugRelatedField(
        queryset=Airport.objects.all(),
        slug_field="closest_big_city",
    )
    destination = serializers.SlugRelatedField(
        queryset=Airport.objects.all(),
        slug_field="closest_big_city",
    )


class RouteRetrieveSerializer(RouteSerializer):
    source = AirportSerializer(read_only=True)
    destination = AirportSerializer(read_only=True)


class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ["id", "name"]


class AirplaneImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = ("id", "image")


class AirplaneSerializer(serializers.ModelSerializer):

    class Meta:
        model = Airplane
        fields = ["id", "name", "rows", "seats_in_row", "capacity", "airplane_type"]


class AirplaneListSerializer(AirplaneSerializer):
    airplane_type = serializers.SlugRelatedField(
        slug_field="name", queryset=AirplaneType.objects.all()
    )

    class Meta:
        model = Airplane
        fields = AirplaneSerializer.Meta.fields + ["image"]
        read_only_fields = ("image",)


class AirplaneRetrieveSerializer(AirplaneListSerializer):
    airplane_type = AirplaneTypeSerializer()


class FlightSerializer(serializers.ModelSerializer):

    class Meta:
        model = Flight
        fields = ["id", "route", "airplane", "departure_time", "arrival_time"]


class FlightListSerializer(FlightSerializer):
    route = serializers.CharField(source="route.cities_route", read_only=True)
    airplane = serializers.CharField(source="airplane.name", read_only=True)
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Flight
        fields = FlightSerializer.Meta.fields + ["tickets_available"]


class TicketSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        data = super(TicketSerializer, self).validate(attrs=attrs)
        Ticket.validate_ticket(
            attrs["row"],
            attrs["seat"],
            attrs["flight"].airplane,
            ValidationError,
        )
        return data

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "flight")


class TicketListSerializer(TicketSerializer):
    flight = FlightListSerializer(read_only=True)


class TicketSeatsSerializer(TicketSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class FlightRetrieveSerializer(FlightSerializer):
    route = RouteRetrieveSerializer()
    airplane = AirplaneRetrieveSerializer()
    crew = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="full_name"
    )
    taken_places = TicketSeatsSerializer(source="tickets", many=True, read_only=True)

    class Meta:
        model = Flight
        fields = FlightSerializer.Meta.fields + ["crew", "taken_places"]


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order


class OrderRetrieveSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True)
