
from datetime import datetime, timedelta
from typing import List, Dict
import math

def parse_hhmm(s: str):
    h, m = map(int, s.split(":"))
    return h, m

# Default opening windows by category (fallback if POI has no hours)
DEFAULT_WINDOWS = {
    "museums": ("10:00", "18:00"),
    "landmarks": ("09:00", "19:00"),
    "nature": ("06:00", "20:00"),
    "views": ("10:00", "22:00"),
    "food": ("11:30", "22:00"),
    "nightlife": ("18:00", "02:00")
}

# Default dwell minutes by category and pace
DEFAULT_DWELL = {
    "chill":   {"museums":120, "landmarks":90, "nature":90, "views":60, "food":60, "nightlife":90},
    "normal":  {"museums":90,  "landmarks":75, "nature":75, "views":50, "food":50, "nightlife":75},
    "packed":  {"museums":75,  "landmarks":60, "nature":60, "views":40, "food":45, "nightlife":60},
}

def walking_minutes_for_km(km: float, speed_kmh: float = 4.5) -> int:
    return int((km / speed_kmh) * 60)

def schedule_day(
    date_str: str,
    ordered_stops: List[Dict],
    distance_fn,
    day_start="09:30",
    day_end="19:00",
    pace="normal",
    insert_lunch=True,
    lunch_time="13:00",
):
    """
    Build a timeline for a single day:
    - respects default time windows by category (fallback)
    - inserts lunch near lunch_time
    - accounts for walking time between stops
    Returns schedule dict with legs and stops including concrete times.
    """
    # Parse start/end
    s_h, s_m = parse_hhmm(day_start); e_h, e_m = parse_hhmm(day_end)
    current = datetime.fromisoformat(f"{date_str} {s_h:02d}:{s_m:02d}:00")
    end_dt = datetime.fromisoformat(f"{date_str} {e_h:02d}:{e_m:02d}:00")
    lunch_dt = datetime.fromisoformat(f"{date_str} {lunch_time}:00")

    # Helper: get dwell
    def dwell_minutes(stop):
        cat = stop.get("category","landmarks")
        return DEFAULT_DWELL.get(pace, DEFAULT_DWELL["normal"]).get(cat, 60)

    # Helper: default window
    def window_for(stop):
        cat = stop.get("category","landmarks")
        open_s, open_e = DEFAULT_WINDOWS.get(cat, ("09:00","19:00"))
        oh, om = parse_hhmm(open_s)
        eh, em = parse_hhmm(open_e)
        # Handle nightlife rollover by clamping to day_end
        open_dt = datetime.fromisoformat(f"{date_str} {oh:02d}:{om:02d}:00")
        close_dt = datetime.fromisoformat(f"{date_str} {eh:02d}:{em:02d}:00")
        if close_dt <= open_dt:
            close_dt = end_dt
        return (open_dt, close_dt)

    legs = []
    visits = []
    total_walk_km = 0.0
    previous = None

    if insert_lunch:
        lunch_taken = False
    else:
        lunch_taken = True

    for stop in ordered_stops:
        # Travel from previous
        if previous is not None:
            km = distance_fn(previous, stop)
            walk_min = walking_minutes_for_km(km)
            legs.append({
                "from": previous["name"],
                "to": stop["name"],
                "depart": current.strftime("%H:%M"),
                "arrive": (current + timedelta(minutes=walk_min)).strftime("%H:%M"),
                "distance_km": round(km,1),
                "mode":"walk"
            })
            current += timedelta(minutes=walk_min)
            total_walk_km += km

        # Lunch insertion
        if not lunch_taken and current >= lunch_dt:
            visits.append({
                "name":"Lunch (nearby)",
                "category":"food",
                "start": current.strftime("%H:%M"),
                "end": (current + timedelta(minutes=45)).strftime("%H:%M"),
                "dwell_min": 45
            })
            current += timedelta(minutes=45)
            lunch_taken = True

        # Respect window
        open_dt, close_dt = window_for(stop)
        if current < open_dt:
            current = open_dt
        if current >= close_dt:
            continue
        dm = dwell_minutes(stop)
        leave = current + timedelta(minutes=dm)
        if leave > close_dt:
            dm = int((close_dt - current).total_seconds()/60)
            if dm < 20:
                continue
            leave = current + timedelta(minutes=dm)

        visits.append({
            "name": stop["name"],
            "category": stop.get("category"),
            "start": current.strftime("%H:%M"),
            "end": leave.strftime("%H:%M"),
            "dwell_min": dm
        })
        current = leave
        previous = stop

        # End-of-day cutoff
        if current >= end_dt:
            break

    return {
        "date": date_str,
        "legs": legs,
        "stops": visits,
        "total_walk_km": round(total_walk_km, 1)
    }
