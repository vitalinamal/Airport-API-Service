import pathlib
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


class Crew(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Airport(models.Model):
    name = models.CharField(max_length=50)
    closest_big_city = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name} ({self.closest_big_city})"


class Route(models.Model):
    source = models.ForeignKey(
        Airport, on_delete=models.CASCADE, related_name="routes_from"
    )
    destination = models.ForeignKey(
        Airport, on_delete=models.CASCADE, related_name="routes_to"
    )
    distance = models.IntegerField()

    class Meta:
        ordering = ["distance"]

    @property
    def cities_route(self):
        return f"{self.source.closest_big_city}-{self.destination.closest_big_city}"

    def __str__(self):
        return f"{self.source.name} - {self.destination.name}"


class AirplaneType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


def airplane_image_path(instance: "Airplane", filename: str) -> pathlib.Path:
    filename = (
        f"{slugify(instance.name)}-{uuid.uuid4()}" + pathlib.Path(filename).suffix
    )
    return pathlib.Path("upload/airplane/") / pathlib.Path(filename)


class Airplane(models.Model):
    name = models.CharField(max_length=50, null=False, blank=False)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()
    airplane_type = models.ForeignKey(
        AirplaneType, on_delete=models.CASCADE, related_name="airplanes"
    )
    image = models.ImageField(null=True, upload_to=airplane_image_path)

    class Meta:
        ordering = ["name"]

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row

    def __str__(self):
        return f"{self.name} ({self.airplane_type.name})"


class Flight(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="flights")
    airplane = models.ForeignKey(
        Airplane, on_delete=models.CASCADE, related_name="flights"
    )
    crew = models.ManyToManyField(Crew, related_name="flights")
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()

    class Meta:
        ordering = ["-departure_time"]

    def __str__(self):
        return (
            f"{self.route.source.name} - {self.route.destination.name} "
            f"({self.departure_time.strftime('%Y-%m-%d %H:%M')} - "
            f"{self.arrival_time.strftime('%Y-%m-%d %H:%M')})"
        )


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.created_at.strftime('%Y-%m-%d %H:%M:%S')} by {self.user}"


class Ticket(models.Model):
    row = models.IntegerField()
    seat = models.IntegerField()
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name="tickets")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="tickets")

    class Meta:
        unique_together = ("flight", "row", "seat")
        ordering = ["row", "seat"]

    def __str__(self):
        return f"Ticket for {self.flight} - Row {self.row}, Seat {self.seat}"

    @staticmethod
    def validate_ticket(row, seat, airplane, error_to_raise):
        for ticket_attr_value, ticket_attr_name, airplane_attr_name in [
            (row, "row", "rows"),
            (seat, "seat", "seats_in_row"),
        ]:
            count_attrs = getattr(airplane, airplane_attr_name)
            if not (1 <= ticket_attr_value <= count_attrs):
                raise error_to_raise(
                    {
                        ticket_attr_name: f"{ticket_attr_name} "
                        f"number must be in available range: "
                        f"(1, {airplane_attr_name}): "
                        f"(1, {count_attrs})"
                    }
                )

    def clean(self):
        Ticket.validate_ticket(
            self.row,
            self.seat,
            self.flight.airplane,
            ValidationError,
        )

    def save(
        self,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        self.full_clean()
        return super(Ticket, self).save(
            force_insert, force_update, using, update_fields
        )
