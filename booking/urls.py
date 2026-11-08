from django.urls import path

from .views import (
    CancelBookingView,
    CompleteBookingView,
    ConfirmBookingView,
    CreateBookingView,
    MyAvailabilityDetailView,
    MyAvailabilityListCreateView,
    MyBookingsView,
    ProviderAvailabilityListView,
    ReceivedBookingsView,
    RejectBookingView,
)

urlpatterns = [
    path("availability/", MyAvailabilityListCreateView.as_view()),
    path("availability/<int:pk>/", MyAvailabilityDetailView.as_view()),
    path("providers/<int:provider_id>/availability/", ProviderAvailabilityListView.as_view()),
    path("book/<int:availability_id>/", CreateBookingView.as_view()),
    path("mine/", MyBookingsView.as_view()),
    path("received/", ReceivedBookingsView.as_view()),
    path("<int:pk>/confirm/", ConfirmBookingView.as_view()),
    path("<int:pk>/reject/", RejectBookingView.as_view()),
    path("<int:pk>/complete/", CompleteBookingView.as_view()),
    path("<int:pk>/cancel/", CancelBookingView.as_view()),
]
