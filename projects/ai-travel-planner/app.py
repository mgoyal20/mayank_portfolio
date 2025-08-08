
import os, math
import streamlit as st
from datetime import date
from typing import List, Dict

from routing.matrix import distance_km
from routing.tsp import tsp_order
from retrieval.places import get_sample_pois
from retrieval.places_google import get_live_pois

st.set_page_config(page_title="AI Travel Planner", page_icon="🗺️", layout="wide")
HAS_GMAPS = bool(os.environ.get("GOOGLE_PLACES_API_KEY") or os.environ.get("GOOGLE_MAPS_API_KEY"))

st.title("🗺️ AI Travel Planner")
st.caption("Google Places retrieval + OR-Tools routing (falls back to samples if no API key).")

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

    # Start near the first POI
    home = {"name":"Hotel", "lat": pois[0]["lat"], "lng": pois[0]["lng"]}
    total_dist = 0.0
    tabs = st.tabs([f"Day {i+1}" for i in range(len(day_lists))])

    for idx, day_stops in enumerate(day_lists):
        with tabs[idx]:
            if len(day_stops) <= 1:
                ordered = day_stops
                dist_km = 0.0
            else:
                ordered, dist_km = tsp_order(day_stops, distance_km, home)
            total_dist += dist_km
            st.markdown(f"**Approx distance (walking): {dist_km:.1f} km**")
            for s in ordered:
                meta = f" · ⭐ {s.get('rating','-')}"
                if s.get('address'): meta += f" · {s['address']}"
                st.markdown(f"- **{s['name']}** · {s['category']}{meta}")
            st.divider()

    ok = total_dist <= max_walk_km * len(day_lists)
    st.success(f"Trip distance: {total_dist:.1f} km · Constraint: ≤ {max_walk_km} km/day × {len(day_lists)} days → {'PASS' if ok else 'ADJUST NEEDED'}")

    st.caption("Distance uses Google Distance Matrix when key is set; otherwise haversine estimate.")
else:
    st.info("Fill the form and click **Generate Itinerary**. Toggle 'Use Google Places' if you've added an API key as a Space secret.")
