from django.urls import path

from .views import CallApplyView, CallListView, CallSaveView, SavedCallListView

urlpatterns = [
    path("", CallListView.as_view(), name="call-list"),
    path("saved/", SavedCallListView.as_view(), name="call-saved"),
    path("<int:pk>/save/", CallSaveView.as_view(), name="call-save"),
    path("<int:pk>/apply/", CallApplyView.as_view(), name="call-apply"),
]
