"""URL routes for the mythical_mane app."""
from django.urls import path

from . import views

app_name = "mythical_mane"

urlpatterns = [
    path("patients/", views.patient_list, name="patient_list"),
]
