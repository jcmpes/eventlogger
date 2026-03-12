from django.contrib import admin
from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["user", "created_at"]
    list_filter = ["user"]
    ordering = ["-created_at"]
