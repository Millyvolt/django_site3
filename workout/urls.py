from django.urls import path
from . import views

app_name = "workout"

urlpatterns = [
    path("", views.SessionListView.as_view(), name="session_list"),
    path("session/<int:pk>/", views.SessionDetailView.as_view(), name="session_detail"),
    path("session/create/", views.SessionCreateView.as_view(), name="session_create"),
    path("session/<int:pk>/update/", views.SessionUpdateView.as_view(), name="session_update"),
    path("session/<int:pk>/delete/", views.SessionDeleteView.as_view(), name="session_delete"),
    path("session/<int:pk>/end/", views.end_session, name="session_end"),
    path("session/<int:session_id>/set/add/", views.set_add, name="set_add"),
    path("exercises/", views.ExerciseListView.as_view(), name="exercise_list"),
]


