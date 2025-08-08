
import streamlit as st
from datetime import date, timedelta
import math
from typing import List, Dict

from routing.matrix import haversine_km
from routing.tsp import nearest_neighbor_order
from retrieval.places import get_sample_pois

st.set_page_config(page_title="AI Travel Planner (MVP)", page_icon="🗺️", layout="wide")

st.title("🗺️ AI Travel Planner (MVP)")
st.caption("MVP demo: no API keys needed. Generates a simple, grounded itinerary with realistic ordering.")

with st.sidebar:
    st.header("Trip details")
    city = st.selectbox("City", ["Las Vegas", "New York", "Tokyo", "Chicago", "San Francisco"])
    start = st.date_input("Start date", value=date.today())
    days = st.slider("Days", 1, 7, 2)
    pace = st.select_slider("Pace", options=["chill", "normal", "packed"], value="normal")
    interests = st.multiselect("Interests", ["landmarks", "museums", "nature", "food", "views", "nightlife"], default=["landmarks","food","views"])
    generate = st.button("Generate Itinerary")

pace_to_max_km = {"chill": 8, "normal": 12, "packed": 16}
max_walk_km = pace_to_max_km.get(pace, 12)

def split_days(stops: List[Dict], num_days: int) -> List[List[Dict]]:
    # Simple split: distribute stops across days
    if num_days <= 0: return [stops]
    per_day = max(2, math.ceil(len(stops)/num_days))
    out = []
    i = 0
    for d in range(num_days):
        out.append(stops[i:i+per_day])
        i += per_day
    if out and len(out[-1]) < 2 and len(out) > 1:  # balance last day
        out[-2].extend(out[-1])
        out = out[:-1]
    return out

if generate:
    st.subheader(f"Itinerary for {city} · {days} day(s) · {pace} pace")
    # 1) Get POIs for the city & interests
    pois = get_sample_pois(city, interests)
    if not pois:
        st.warning("No POIs found for this city/interests in the MVP sample. Try different interests.")
        st.stop()

    # 2) Split across days
    day_lists = split_days(pois, days)

    # 3) Order within each day using nearest-neighbor
    home = {"name":"Hotel", "lat": pois[0]["lat"], "lng": pois[0]["lng"]}  # crude: start near first POI
    total_walk = 0.0
    tabs = st.tabs([f"Day {i+1}" for i in range(len(day_lists))])
    for idx, day_stops in enumerate(day_lists):
        with tabs[idx]:
            if len(day_stops) <= 1:
                ordered = day_stops
                dist_km = 0.0
            else:
                ordered, dist_km = nearest_neighbor_order(home, day_stops, distance_fn=haversine_km)
            total_walk += dist_km
            st.markdown(f"**Walking distance (approx): {dist_km:.1f} km**")

            for s in ordered:
                st.markdown(f"- **{s['name']}** · {s['category']} · ⭐ {s['rating']} · {s.get('note','')}")
            st.divider()

    # 4) Simple constraint check
    ok = total_walk <= max_walk_km * len(day_lists)
    st.success(f"Total distance across trip: {total_walk:.1f} km · Constraint: ≤ {max_walk_km} km/day × {len(day_lists)} days → {'PASS' if ok else 'ADJUST NEEDED'}")

    st.caption("Note: This MVP uses sample POIs and a greedy routing heuristic to stay key-free and fast. Next steps: plug in Places API, time windows, and LLM planner + RAG.")
else:
    st.info("Fill the form on the left and click **Generate Itinerary**. This key-free MVP uses a small curated POI set and a greedy router to produce a plausible itinerary quickly.")

