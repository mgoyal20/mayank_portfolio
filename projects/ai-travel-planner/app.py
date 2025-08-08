import os, math, io
import streamlit as st
from datetime import date, timedelta
from typing import List, Dict, Optional
from urllib.parse import quote, unquote

from routing.matrix import distance_km
from routing.tsp import tsp_order
from retrieval.places import get_sample_pois
from retrieval.places_google import (
    get_live_pois,
    get_place_details_bulk,
    get_nearby_food,
)
from planner.schedule import schedule_day
from utils.pdf_export import itinerary_to_pdf

st.set_page_config(page_title="AI Travel Planner", page_icon="🗺️", layout="wide")
HAS_GMAPS = bool(os.environ.get("GOOGLE_PLACES_API_KEY") or os.environ.get("GOOGLE_MAPS_API_KEY"))

# --- URL state (shareable links) ---
qp = st.query_params()
def _get(name, default):
    v = qp.get(name)
    if not v: return default
    if isinstance(default, list):
        return [unquote(x) for x in v[0].split(",") if x]
    if isinstance(default, int):
        try: return int(v[0])
        except: return default
    return unquote(v[0])

CITY_CHOICES = ["Las Vegas", "New York", "Tokyo", "Chicago", "San Francisco"]
city_default = _get("city", "Las Vegas")
days_default = _get("days", 2)
pace_default = _get("pace", "normal")
interests_default = _get("interests", ["landmarks","food","views"])

with st.sidebar:
    st.header("Trip details")
    city = st.selectbox("City", CITY_CHOICES, index=CITY_CHOICES.index(city_default) if city_default in CITY_CHOICES else 0)
    start = st.date_input("Start date", value=date.today())
    days = st.slider("Days", 1, 7, days_default if 1 <= days_default <= 7 else 2)
    pace = st.select_slider("Pace", options=["chill","normal","packed"], value=pace_default if pace_default in ["chill","normal","packed"] else "normal")
    interests = st.multiselect("Interests", ["landmarks","museums","nature","food","views","nightlife"], default=interests_default)
    use_live = st.checkbox("Use Google Places (if key available)", value=HAS_GMAPS, disabled=not HAS_GMAPS)

    # Keep URL in sync
    st.experimental_set_query_params(
        city=city, days=str(days), pace=pace,
        interests=",".join(quote(i) for i in interests)
    )

# Global constraint
pace_to_max_km = {"chill": 8, "normal": 12, "packed": 16}
max_walk_km = pace_to_max_km.get(pace, 12)

def split_days(stops: List[Dict], num_days: int) -> List[List[Dict]]:
    if num_days <= 0: return [stops]
    per_day = max(2, math.ceil(len(stops)/num_days))
    out, i = [], 0
    for _ in range(num_days):
        out.append(stops[i:i+per_day])
        i += per_day
    if out and len(out[-1]) < 2 and len(out) > 1:
        out[-2].extend(out[-1]); out = out[:-1]
    return out

# ————— UI actions —————
colA, colB, colC = st.columns([1,1,1])
with colA:
    generate = st.button("Generate Itinerary", type="primary")
with colB:
    export_pdf = st.button("Export to PDF", help="Generates a shareable PDF")
with colC:
    st.caption(f"Walking limit: ≤ {max_walk_km} km/day")

# Session state for swap
if "last_itinerary" not in st.session_state:
    st.session_state["last_itinerary"] = None
if "raw_pois" not in st.session_state:
    st.session_state["raw_pois"] = []

def lunch_finder(prev_stop):
    # If we have a key, use Nearby Search around the previous stop
    if prev_stop and HAS_GMAPS:
        candidates = get_nearby_food(prev_stop["lat"], prev_stop["lng"], limit=5)
        return candidates[0] if candidates else None
    # Fallback: pick a food POI closest to prev_stop from our retrieved list
    try:
        foodies = [p for p in st.session_state["raw_pois"] if p.get("category") == "food"]
        if prev_stop and foodies:
            best = min(foodies, key=lambda f: distance_km(prev_stop, f))
            return best
    except Exception:
        pass
    return None

def build_itinerary(pois: List[Dict]) -> Dict:
    """Builds a full itinerary dict with days -> route + schedule."""
    day_lists = split_days(pois, days)
    all_days = []
    total_dist = 0.0

    for d_idx, day_stops in enumerate(day_lists):
        # Route
        if len(day_stops) <= 1:
            ordered, dist_km = day_stops, 0.0
        else:
            home = {"name":"Hotel", "lat": day_stops[0]["lat"], "lng": day_stops[0]["lng"]}
            ordered, dist_km = tsp_order(day_stops, distance_km, home)

        # Schedule with time windows + lunch
        the_date = (start + timedelta(days=d_idx)).isoformat()
        sched = schedule_day(
            date_str=the_date,
            ordered_stops=ordered,
            distance_fn=distance_km,
            day_start="09:30",
            day_end="19:00",
            pace=pace,
            insert_lunch=True,
            lunch_time="13:00",
            lunch_finder=lunch_finder
        )
        total_dist += sched["total_walk_km"]
        all_days.append({"date": the_date, "route": ordered, "schedule": sched})

    return {"city": city, "days": days, "pace": pace, "start": start.isoformat(),
            "max_walk_km": max_walk_km, "total_km": round(total_dist,1),
            "days_detail": all_days}

# ————— Generate itinerary —————
if generate:
    # 1) Retrieve POIs
    if use_live and HAS_GMAPS:
        pois = get_live_pois(city, interests, limit=30)
        # Enrich with opening hours if available
        place_ids = [p["place_id"] for p in pois if p.get("place_id")]
        if place_ids:
            details_map = get_place_details_bulk(place_ids)
            # attach opening_hours to each POI when available
            for p in pois:
                det = details_map.get(p.get("place_id"))
                if det:
                    p["opening_hours"] = det.get("opening_hours")
    else:
        pois = get_sample_pois(city, interests)

    if not pois:
        st.warning("No POIs found. Try different interests or disable Google Places.")
        st.stop()

    st.session_state["raw_pois"] = pois

    # 2) Build itinerary
    itinerary = build_itinerary(pois)
    st.session_state["last_itinerary"] = itinerary

# ————— Swap stop UI —————
if st.session_state["last_itinerary"]:
    itin = st.session_state["last_itinerary"]
    st.subheader(f"Itinerary for {itin['city']} · {itin['days']} day(s) · {itin['pace']} pace")
    st.caption(f"Trip distance: {itin['total_km']} km • Constraint: ≤ {itin['max_walk_km']} km/day")

    # Day tabs
    tabs = st.tabs([f"Day {i+1}" for i in range(len(itin["days_detail"]))])

    for d_idx, day in enumerate(itin["days_detail"]):
        with tabs[d_idx]:
            sched = day["schedule"]
            st.markdown(f"**Walking distance (approx): {sched['total_walk_km']:.1f} km**")

            for leg in sched["legs"]:
                st.caption(f"Walk {leg['distance_km']} km · {leg['from']} → {leg['to']} [{leg['depart']} → {leg['arrive']}]")
            for s in sched["stops"]:
                extras = []
                if s.get("dwell_min"): extras.append(f"{s['dwell_min']} min")
                st.markdown(f"- **{s['name']}** · {s.get('category','')} [{s['start']}–{s['end']}] {'· ' + ', '.join(extras) if extras else ''}")

            # Swap controls
            st.divider()
            st.markdown("**Swap a stop**")
            current_names = [s["name"] for s in day["schedule"]["stops"] if not s["name"].startswith("Lunch")]
            if current_names:
                to_replace = st.selectbox(f"Pick a stop to replace (Day {d_idx+1})", current_names, key=f"rep_{d_idx}")
                # Candidates: all raw pois not currently in the day by name
                current_set = set(current_names)
                candidates = [p for p in st.session_state["raw_pois"] if p["name"] not in current_set]
                cand_names = [c["name"] for c in candidates] or ["(no candidates)"]
                replacement = st.selectbox("Replace with", cand_names, key=f"cand_{d_idx}")
                if st.button("Swap and re-route this day", key=f"swap_{d_idx}", disabled=(replacement == "(no candidates)")):
                    # Build new day stop list by replacing the chosen name with the candidate
                    chosen = next((c for c in candidates if c["name"] == replacement), None)
                    if chosen:
                        # Reconstruct day_stops from route base instead of schedule (schedule has Lunch)
                        base_stops = [r for r in day["route"]]
                        # If replacement target not in route (edge case), do nothing
                        if any(s["name"] == to_replace for s in base_stops):
                            for i, s in enumerate(base_stops):
                                if s["name"] == to_replace:
                                    base_stops[i] = chosen
                                    break
                            # Rebuild just this day
                            home = {"name":"Hotel", "lat": base_stops[0]["lat"], "lng": base_stops[0]["lng"]} if base_stops else None
                            if base_stops and len(base_stops) > 1:
                                new_route, _ = tsp_order(base_stops, distance_km, home)
                            else:
                                new_route = base_stops
                            new_sched = schedule_day(
                                date_str=day["date"],
                                ordered_stops=new_route,
                                distance_fn=distance_km,
                                day_start="09:30",
                                day_end="19:00",
                                pace=pace,
                                insert_lunch=True,
                                lunch_time="13:00",
                                lunch_finder=lunch_finder
                            )
                            # Write back into itinerary
                            itin["days_detail"][d_idx]["route"] = new_route
                            itin["days_detail"][d_idx]["schedule"] = new_sched
                            # Update totals
                            itin["total_km"] = round(sum(d["schedule"]["total_walk_km"] for d in itin["days_detail"]), 1)
                            st.session_state["last_itinerary"] = itin
                            st.success("Day updated. Scroll up to see the new order and times.")
            else:
                st.caption("No swappable stops on this day.")

# ————— Export PDF —————
if export_pdf:
    itin = st.session_state.get("last_itinerary")
    if not itin:
        st.warning("Generate an itinerary first.")
    else:
        pdf_bytes = itinerary_to_pdf(itin)
        st.download_button(
            label="Download itinerary.pdf",
            data=pdf_bytes,
            file_name=f"itinerary_{itin['city'].replace(' ','_')}.pdf",
            mime="application/pdf"
        )
