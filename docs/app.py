import io, random, string
from datetime import datetime, timedelta
from dateutil import parser as dtparse
from flask import Flask, render_template, request, send_file, url_for
from flask_wtf import CSRFProtect
from sqlalchemy import create_engine, select, and_
from sqlalchemy.orm import sessionmaker

from models import Scan, Base
from heatmap import render_heatmap

# --- Flask + CSRF ---
app = Flask(__name__)
app.config["SECRET_KEY"] = "change-me-very-secret"  # replace later
csrf = CSRFProtect(app)

# --- DB ---
engine = create_engine("sqlite:///wifi.db", future=True)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine, future=True)

PAGE_SIZE = 50

# -------- utilities ----------
def _clean_str(s, maxlen=64):
    if not s: return None
    s = s.strip()
    return s[:maxlen]

def _clean_channel(ch):
    if ch is None or ch == "":
        return None
    try:
        ch = int(ch)
        if 0 < ch < 200:
            return ch
    except Exception:
        pass
    return None

def _parse_time(s):
    if not s: return None
    try:
        # accepts '2025-08-20T12:30' or ISO strings
        return dtparse.parse(s)
    except Exception:
        return None

def _current_filters():
    return {
        "ssid": _clean_str(request.args.get("ssid")),
        "bssid_hash": _clean_str(request.args.get("bssid_hash")),
        "channel": _clean_channel(request.args.get("channel")),
        "start": _parse_time(request.args.get("start")),
        "end": _parse_time(request.args.get("end")),
        "page": int(request.args.get("page", 1))
    }

def _apply_filters(q, f):
    conds = []
    if f["ssid"]:
        conds.append(Scan.ssid == f["ssid"])
    if f["bssid_hash"]:
        conds.append(Scan.bssid_hash == f["bssid_hash"])
    if f["channel"] is not None:
        conds.append(Scan.channel == f["channel"])
    if f["start"]:
        conds.append(Scan.ts >= f["start"])
    if f["end"]:
        conds.append(Scan.ts <= f["end"])
    return q.filter(and_(*conds)) if conds else q

# -------- seed route (for demo evidence) ----------
@app.get("/seed")
def seed():
    """Seed synthetic data quickly: /seed?rows=2000"""
    rows = request.args.get("rows", "2000")
    try:
        rows = max(100, min(20000, int(rows)))
    except:
        rows = 2000

    ssids = ["UTS-Visitor","UTS-Staff","Lab-AP","CampusNet"]
    channels = [1,6,11,36,40,44,149,153]
    now = datetime.utcnow()

    session = Session()
    count = 0
    for _ in range(rows):
        ssid = random.choice(ssids)
        bssid_hash = "".join(random.choices(string.hexdigits.lower(), k=12))
        ch = random.choice(channels)
        ts = now - timedelta(minutes=random.randint(0, 10000))
        rssi = random.randint(-85, -35)
        # fake coords near UTS Central
        lat = -33.883 + random.uniform(-0.002, 0.002)
        lon = 151.200 + random.uniform(-0.002, 0.002)
        session.add(Scan(ssid=ssid, bssid_hash=bssid_hash, channel=ch, ts=ts,
                         rssi=rssi, lat=lat, lon=lon))
        count += 1
        if count % 1000 == 0:
            session.commit()
    session.commit()
    session.close()
    return f"Seeded {rows} rows."

# -------- reports with filters + pagination ----------
@app.get("/reports")
def reports():
    f = _current_filters()
    session = Session()

    q = session.query(Scan)
    q = _apply_filters(q, f)

    total = q.count()
    page = max(1, f["page"])
    offset = (page - 1) * PAGE_SIZE
    items = q.order_by(Scan.ts.desc()).offset(offset).limit(PAGE_SIZE).all()

    # make a small list for heatmap preview
    sample_for_heat = q.limit(2000).all()
    points = [(s.lat, s.lon, s.rssi) for s in sample_for_heat]
    heat_path = render_heatmap(points)  # 150 dpi default

    # Build link for Export PDF with current filters (GET is fine for demo)
    params = {
        "ssid": f["ssid"] or "",
        "bssid_hash": f["bssid_hash"] or "",
        "channel": f["channel"] or "",
        "start": request.args.get("start",""),
        "end": request.args.get("end",""),
    }
    export_url = url_for("export_pdf", **params)

    return render_template(
        "reports.html",
        items=items,
        total=total,
        page=page,
        page_size=PAGE_SIZE,
        filters=f,
        heat_rel_path=heat_path,     # e.g., static/img/heat_abc.png
        export_url=export_url
    )

# -------- export PDF with parameters block ----------
@app.get("/export-pdf")
def export_pdf():
    f = _current_filters()
    session = Session()
    q = _apply_filters(session.query(Scan), f)
    sample = q.limit(5000).all()
    points = [(s.lat, s.lon, s.rssi) for s in sample]
    heat_path = render_heatmap(points, dpi=150)

    # Prepare PDF in memory
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4

    # Header
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, H-2*cm, "WiFi Analytics Report – PDF v2")
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, H-2.6*cm, f"Generated: {datetime.utcnow().isoformat()}Z")

    # Parameters block
    y = H-3.6*cm
    c.setFont("Helvetica", 10)
    lines = [
        f"Filters:",
        f"  SSID = {f['ssid'] or '∅'}",
        f"  BSSID hash = {f['bssid_hash'] or '∅'}",
        f"  Channel = {f['channel'] if f['channel'] is not None else '∅'}",
        f"  Time range = {f['start'] or '∅'}  →  {f['end'] or '∅'}",
        f"Rows considered for heatmap: {len(sample)}"
    ]
    for line in lines:
        c.drawString(2*cm, y, line)
        y -= 0.5*cm

    # Heatmap image
    # render_heatmap() saved to static/img/..., so we draw it scaled
    img_w = W - 4*cm
    img_h = 9*cm
    c.drawImage(heat_path, 2*cm, y - img_h, width=img_w, height=img_h, preserveAspectRatio=True, mask='auto')
    y -= (img_h + 0.5*cm)

    # Footer (policy note)
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(2*cm, 1.5*cm, "MACs pseudonymised; scan under written permission.")

    c.showPage()
    c.save()
    buf.seek(0)
    filename = "Report_v2_" + datetime.utcnow().strftime("%Y-%m-%d_%H%M") + ".pdf"
    return send_file(buf, as_attachment=True, download_name=filename, mimetype="application/pdf")

@app.get("/")
def home():
    return "<p>Go to <a href='/reports'>/reports</a></p>"

if __name__ == "__main__":
    # For local/Replit runs
    app.run(host="0.0.0.0", port=5000, debug=True)
