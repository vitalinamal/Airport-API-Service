from rest_framework import routers
from django.urls import path, include
from flight.views import (
    CrewViewSet,
    AirportViewSet,
    RouteViewSet,
    AirplaneTypeViewSet,
    AirplaneViewSet,
    FlightViewSet,
    OrderViewSet,
)

router = routers.DefaultRouter()
router.register("crew", CrewViewSet, basename="crew")
router.register("airports", AirportViewSet, basename="airports")
router.register("routs", RouteViewSet, basename="routs")
router.register("airplane_type", AirplaneTypeViewSet, basename="airplane_type")
router.register("airplanes", AirplaneViewSet, basename="airplanes")
router.register("flights", FlightViewSet, basename="flights")
router.register("orders", OrderViewSet, basename="orders")

urlpatterns = [
    path('', include(router.urls)),
]

app_name = 'flight'
