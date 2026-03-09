import json
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.db.models.functions import TruncMinute
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from .models import DeletedEvent
from .models import Event


@login_required
def dashboard(request):
    last = (
        Event.objects
        .filter(user=request.user)
        .order_by("-created_at")
        .first()
    )

    if last:
        delta = timezone.now() - last.created_at
        minutes = int(delta.total_seconds() / 60)
        last_event = f"hace {minutes} min"
    else:
        last_event = "nunca"

    return render(
        request, "tracker/dashboard.html", {
            "last_event": last_event,
            "last_event_ts": last.created_at.isoformat() if last else "",
        },
    )


@login_required
def events_table(request):
    events = (
        Event.objects
        .filter(user=request.user)
        .order_by("-created_at")
    )

    rows = []

    prev = None

    for e in events:
        if prev:

            diff = prev.created_at - e.created_at
            minutes = int(diff.total_seconds() / 60)

            if minutes > 60:
                break

        else:
            minutes = None

        dots = min(minutes, 15) if minutes else 0

        rows.append({
            "time": timezone.localtime(e.created_at),
            "gap": minutes,
            "dots": range(dots),
            "overflow": minutes > 15 if minutes else False,
        })

        prev = e

    return render(
        request,
        "tracker/partials/events_table.html",
        {"rows": rows}
    )


@login_required
def log_event(request):
    Event.objects.create(user=request.user)

    response = HttpResponse("")
    response["HX-Trigger"] = "eventLogged"

    return response


@login_required
def undo_event(request):
    event = Event.objects.filter(user=request.user).order_by("-created_at").first()

    if event:
        DeletedEvent.objects.create(
            user=request.user,
            created_at=event.created_at
        )
        event.delete()

    new_last_event = Event.objects.filter(user=request.user).order_by("-created_at").first()
    response = HttpResponse("")
    response["HX-Trigger"] = json.dumps({
        "eventUndo": {
            "ts": new_last_event.created_at.isoformat() if new_last_event else "",
        }
    })

    return response


@login_required
def redo_event(request):
    event = DeletedEvent.objects.filter(user=request.user).order_by("-created_at").first()

    if event:
        Event.objects.create(
            user=request.user,
            created_at=event.created_at
        )
        event.delete()

    response = HttpResponse("")
    response["HX-Trigger"] = json.dumps({
        "eventRedo": {
            "ts": event.created_at.isoformat() if event else "",
        }
    })

    return response


@login_required
def chart(request):
    now = timezone.now()
    start = now - timedelta(hours=1)

    qs = (
        Event.objects
        .filter(user=request.user, created_at__gte=start)
        .annotate(minute=TruncMinute("created_at"))
        .values("minute")
        .annotate(count=Count("id"))
        .order_by("minute")
    )

    counts = {row["minute"]: row["count"] for row in qs}

    labels = []
    data = []

    current = start.replace(second=0, microsecond=0)

    while current <= now:
        labels.append(current.strftime("%H:%M"))
        data.append(counts.get(current, 0))

        current += timedelta(minutes=1)

    return render(request, "tracker/partials/chart.html", {
        "chart_labels": json.dumps(labels),
        "chart_data": json.dumps(data),
    })
