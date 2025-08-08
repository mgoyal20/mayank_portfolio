from datetime import datetime, timedelta
from typing import List, Dict, Callable, Optional

def parse_hhmm(s: str):
    h, m = map(int, s.split(":"))
    return h, m

# Fallback opening windows (used if a stop has no detailed hours)
DEFAULT_WINDOWS = {
    "museums": ("10:00", "18:00"),
    "landmarks": ("09:00", "19:00"),
    "nature": ("06:00", "20:00"),
    "views": ("10:00", "22:00"),
    "food": ("11:30", "22:00"),
    "nightlife": ("18:00", "02:00")  # rolls over midnight
}

# Dwell minutes by pace/category
DEFAULT_DWELL = {
    "chill":   {"museums":120, "landmarks":90, "nature":90, "views":60, "food":60, "nightlife":90},
    "normal":  {"museums":90,  "landmarks":75, "nature":75, "views":50, "food":50, "nightlife":75},
    "packed":  {"museums":75,  "landmarks":60, "nature":60, "views":40, "food":45, "nightlife":60},
}

def walking_minutes_for_km(km: float, speed_kmh: float = 4.5) -> int:
    return int((km / speed_kmh) * 60)

def _hours_from_details(stop: Dict, date_str: str):
    """
    If Google Place Details provided opening_hours with 'periods' or 'weekday_text',
    compute open/close for this weekday. Fallback to defaults if absent.
    """
    oh = stop.get("opening_hours")
    if not oh:
        return None

    # weekday_text like ["Monday: 9 AM–5 PM", ...] is hard to parse reliably here.
    # Prefer 'periods' with 'open'/'close' times if present.
    periods = oh.get("periods")
    if not periods:
        return None

    weekday = datetime.fromisoformat(f"{date_str} 00:00:00").weekday()  # Mon=0..Sun=6
    # Find a period that matches today's weekday
    candidates = [p for p in periods if p.get("open", {}).get("day") == weekday]
    if not candidates:
        return None

    def hhmm_from_google(t: str):
        # "0930" → "09:30"
        t = t.zfill(4)
        return f"{t[:2]}:{t[2:]}"
    # Pick first period
    p = candidates[0]
    open_time = hhmm_from_google(p.get("open", {}).get("time", "0900"))
    close_time = hhmm_from_google(p.get("close", {}).get("time", "1900")) if p.get("close") else "1900"

    return (open_time, close_time)

def schedule_day(
    date_str: str,
    ordered_stops: List[Dict],
    distance_fn: Callable,
    day_start="09:30",
    day_end="19:00",
    pace="normal",
    insert_lunch=True,
    lunch_time="13:00",
    lunch_finder: Optional[Callable] = None
) -> Dict:
    s_h, s_m = parse_hhmm(day_start); e_h, e_m = parse_hhmm(day_end)
    current = datetime.fromisoformat(f"{date_str} {s_h:02d}:{s_m:02d}:00")
    end_dt = datetime.fromisoformat(f"{date_str} {e_h:02d}:{e_m:02d}:00")
    lunch_dt = datetime.fromisoformat(f"{date_str} {lunch_time}:00")

    def dwell_minutes(stop):
        cat = stop.get("category","landmarks")
        return DEFAULT_DWELL.get(pace, DEFAULT_DWELL["normal"]).get(cat, 60)

    def window_for(stop):
        # If hours from details exist, use them
        det = _hours_from_details(stop, date_str)
        if det:
            open_s, open_e = det
        else:
            cat = stop.get("category","landmarks")
            open_s, open_e = DEFAULT_WINDOWS.get(cat, ("09:00","19:00"))

        oh, om = parse_hhmm(open_s)
        eh, em = parse_hhmm(open_e)
        open_dt = datetime.fromisoformat(f"{date_str} {oh:02d}:{om:02d}:00")
        close_dt = datetime.fromisoformat(f"{date_str} {eh:02d}:{em:02d}:00")
        if close_dt <= open_dt:
            close_dt = end_dt  # roll over midnight → clamp
        return (open_dt, close_dt)

    legs, visits = [], []
    total_walk_km = 0.0
    previous = None
    lunch_taken = not insert_lunch

    for stop in ordered_stops:
        # Travel from previous
        if previous is not None:
            km = distance_fn(previous, stop)
            walk_min = walking_minutes_for_km(km)
            legs.append({
                "from": previous["name"], "to": stop["name"],
                "depart": current.strftime("%H:%M"),
                "arrive": (current + timedelta(minutes=walk_min)).strftime("%H:%M"),
                "distance_km": round(km,1), "mode":"walk"
            })
            current += timedelta(minutes=walk_min)
            total_walk_km += km

        # Lunch
        if not lunch_taken and current >= lunch_dt:
            chosen = None
            if lunch_finder:
                chosen = lunch_finder(previous) if previous else None
            if chosen:
                visits.append({
                    "name": chosen["name"], "category":"food",
                    "start": current.strftime("%H:%M"),
                    "end": (current + timedelta(minutes=45)).strftime("%H:%M"),
                    "dwell_min": 45
                })
            else:
                visits.append({
                    "name":"Lunch (nearby)", "category":"food",
                    "start": current.strftime("%H:%M"),
                    "end": (current + timedelta(minutes=45)).strftime("%H:%M"),
                    "dwell_min": 45
                })
            current += timedelta(minutes=45)
            lunch_taken = True

        # Windows
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
            "name": stop["name"], "category": stop.get("category"),
            "start": current.strftime("%H:%M"), "end": leave.strftime("%H:%M"),
            "dwell_min": dm
        })
        current = leave
        previous = stop
        if current >= end_dt:
            break

    return {"date": date_str, "legs": legs, "stops": visits, "total_walk_km": round(total_walk_km, 1)}
