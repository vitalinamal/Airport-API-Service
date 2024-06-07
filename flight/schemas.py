from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from flight.serializers import (
    FlightListSerializer,
    FlightRetrieveSerializer,
    FlightSerializer,
)

flight_schema = extend_schema_view(
    list=extend_schema(
        description="Retrieve a list of flights. Allows filtering by route, airport, and date.",
        parameters=[
            OpenApiParameter(
                name="route",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by route (source-destination). Example: 'Paris-Kyiv'",
                required=False,
            ),
            OpenApiParameter(
                name="airport",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by airport's closest big city. Example: 'Rome'",
                required=False,
            ),
            OpenApiParameter(
                name="date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Filter by departure date. Format: 'YYYY-MM-DD'",
                required=False,
            ),
        ],
        responses={
            200: FlightListSerializer(many=True),
            400: "Bad Request - Invalid filter parameters.",
            401: "Unauthorized - Authentication credentials were not provided or are invalid.",
            403: "Forbidden - You do not have permission to perform this action.",
        },
    ),
    retrieve=extend_schema(
        description="Retrieve details of a specific flight.",
        responses={
            200: FlightRetrieveSerializer,
            401: "Unauthorized - Authentication credentials were not provided or are invalid.",
            403: "Forbidden - You do not have permission to perform this action.",
            404: "Not Found - Flight not found.",
        },
    ),
    create=extend_schema(
        description="Create a new flight.",
        responses={
            201: FlightSerializer,
            400: "Bad Request - Invalid data provided.",
            401: "Unauthorized - Authentication credentials were not provided or are invalid.",
            403: "Forbidden - You do not have permission to perform this action.",
        },
    ),
    update=extend_schema(
        description="Update an existing flight.",
        responses={
            200: FlightSerializer,
            400: "Bad Request - Invalid data provided.",
            401: "Unauthorized - Authentication credentials were not provided or are invalid.",
            403: "Forbidden - You do not have permission to perform this action.",
            404: "Not Found - Flight not found.",
        },
    ),
    partial_update=extend_schema(
        description="Partially update an existing flight.",
        responses={
            200: FlightSerializer,
            400: "Bad Request - Invalid data provided.",
            401: "Unauthorized - Authentication credentials were not provided or are invalid.",
            403: "Forbidden - You do not have permission to perform this action.",
            404: "Not Found - Flight not found.",
        },
    ),
    destroy=extend_schema(
        description="Delete an existing flight.",
        responses={
            204: None,
            401: "Unauthorized - Authentication credentials were not provided or are invalid.",
            403: "Forbidden - You do not have permission to perform this action.",
            404: "Not Found - Flight not found.",
        },
    ),
)
