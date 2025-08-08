import os, math
import streamlit as st
from datetime import date, timedelta
from typing import List, Dict

from routing.matrix import distance_km
from routing.tsp import tsp_order
from retrieval.places import get_sample_pois
from retrieval.places_google import get_live_pois
from planner.schedule import schedule_day

st.set_page_config(page_title="AI Travel Planner", page_icon="🗺️", layout="wide")
HAS_GMAPS = bool(os.environ.get("GOOGLE_PLACES_API_KEY") or os.environ.get("GOOGLE_MAPS_API_KEY"))

st.title("🗺️ AI Travel Planner")
st.caption("Time windows + lunch slots. Uses Google Places/Distance Matrix if keys are set; otherwise sample data + haversine.")

with st.sidebar:
    st.header("Trip details")
    city = st.selectbox("City", ["Las Vegas", "New York", "Tokyo", "Chicago", "San Francisco"])
    start = st.date_input("Start date", value=date.today())
    days = st.slider("Days", 1, 7, 2)
    pace = st.select_slider("Pace", options=["chill", "normal", "packed"], value="normal")
    interests = st.multiselect("Interests", ["landmarks", "museums", "nature", "food", "views", "nightlife"], default=["landmarks","food","views"])
    use_live = st.checkbox("Use Google Places (if key available)", value=HAS_GMAPS, disabled=not HAS_GMAPS)
    generate = st.button("Generate Itinerary")

pace_to_max_km = {"chill": 8, "normal": 12, "packed": 16}
max_walk_km = pace_to_max_km.get(pace, 12)

def split_days(stops: List[Dict], num_days: int) -> List[List[Dict]]:
    if num_days <= 0: return [stops]
    per_day = max(2, math.ceil(len(stops)/num_days))
    out = []
    i = 0
    for _ in range(num_days):
        out.append(stops[i:i+per_day])
        i += per_day
    if out and len(out[-1]) < 2 and len(out) > 1:
        out[-2].extend(out[-1])
        out = out[:-1]
    return out

if generate:
    st.subheader(f"Itinerary for {city} · {days} day(s) · {pace} pace")

    # 1) Retrieve POIs
    if use_live and HAS_GMAPS:
        pois = get_live_pois(city, interests, limit=30)
        st.caption(f"Loaded {len(pois)} POIs from Google Places API.")
    else:
        pois = get_sample_pois(city, interests)
        st.caption(f"Loaded {len(pois)} sample POIs (no API keys used).")

    if not pois:
        st.warning("No POIs found. Try different interests or disable Google Places.")
        st.stop()

    # 2) Split across days
    day_lists = split_days(pois, days)
    total_dist = 0.0

    tabs = st.tabs([f"Day {i+1}" for i in range(len(day_lists))])
    for d_idx, day_stops in enumerate(day_lists):
        with tabs[d_idx]:
            if len(day_stops) <= 1:
                ordered = day_stops
                dist_km = 0.0
            else:
                home = {"name":"Hotel", "lat": day_stops[0]["lat"], "lng": day_stops[0]["lng"]}
                ordered, dist_km = tsp_order(day_stops, distance_km, home)

            the_date = (start + timedelta(days=d_idx)).isoformat()
            schedule = schedule_day(
                date_str=the_date,
                ordered_stops=ordered,
                distance_fn=distance_km,
                day_start="09:30",
                day_end="19:00",
                pace=pace,
                insert_lunch=True,
                lunch_time="13:00"
            )
            total_dist += schedule["total_walk_km"]

            st.markdown(f"**Walking distance (approx): {schedule['total_walk_km']:.1f} km**")
            for leg in schedule["legs"]:
                st.caption(f"Walk {leg['distance_km']} km · {leg['from']} → {leg['to']} [{leg['depart']} → {leg['arrive']}]")
            for s in schedule["stops"]:
                st.markdown(f"- **{s['name']}** · {s['category']} [{s['start']}–{s['end']}]")

            ok = schedule["total_walk_km"] <= max_walk_km
            st.success(f"Day {d_idx+1}: {'PASS' if ok else 'ADJUST NEEDED'} (limit {max_walk_km} km)")    

    st.info(f"Trip total distance: {total_dist:.1f} km (limit {max_walk_km} km/day × {len(day_lists)} days)")
else:
    st.info("Fill the form and click **Generate Itinerary**. The planner respects opening windows by category and adds lunch at ~13:00.")
