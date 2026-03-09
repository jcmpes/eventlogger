from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("log/", views.log_event, name="log"),
    path("undo/", views.undo_event, name="undo"),
    path("redo/", views.redo_event, name="redo"),
    path("events-table/", views.events_table, name="events_table"),
    path("chart/", views.chart, name="chart"),
]