from fpdf import FPDF
from typing import Dict, List
from datetime import datetime

def itinerary_to_pdf(itin: Dict) -> bytes:
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    # Header
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"Itinerary – {itin['city']}", ln=1)
    pdf.set_font("Helvetica", "", 11)
    start = itin.get("start", "")
    pdf.cell(0, 6, f"Days: {itin['days']}   Pace: {itin['pace']}   Start: {start}", ln=1)
    pdf.cell(0, 6, f"Total walking: {itin['total_km']} km   Limit: ≤ {itin['max_walk_km']} km/day", ln=1)
    pdf.ln(2)

    for idx, day in enumerate(itin["days_detail"]):
        pdf.set_font("Helvetica", "B", 13)
        dt = day.get("date", "")
        try:
            dt_str = datetime.fromisoformat(dt).strftime("%a, %b %d, %Y")
        except Exception:
            dt_str = dt
        pdf.cell(0, 8, f"Day {idx+1} – {dt_str}", ln=1)

        sched = day["schedule"]
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 6, f"Distance: {sched['total_walk_km']} km", ln=1)

        # Legs
        for leg in sched.get("legs", []):
            pdf.set_font("Helvetica", "I", 10)
            pdf.multi_cell(0, 5, f"Walk {leg['distance_km']} km: {leg['from']} → {leg['to']} [{leg['depart']}–{leg['arrive']}]")

        # Stops
        for s in sched.get("stops", []):
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 6, f"{s['start']}-{s['end']}: {s['name']}", ln=1)
            pdf.set_font("Helvetica", "", 10)
            cat = s.get("category","")
            if cat:
                pdf.cell(0, 5, f"  • {cat}", ln=1)

        pdf.ln(2)

    return bytes(pdf.output(dest="S").encode("latin1"))
