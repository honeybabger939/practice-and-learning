import os, uuid
import numpy as np
import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt

def get_colormap():
    # Centralised colormap so UI and PDF match
    return plt.cm.inferno

def render_heatmap(points, out_dir="static/img", dpi=150):
    """
    points: list of (lat, lon, rssi) floats. If you don't have lat/lon,
    we fall back to an RSSI histogram (still valid evidence).
    """
    os.makedirs(out_dir, exist_ok=True)
    fname = f"heat_{uuid.uuid4().hex}.png"
    out_path = os.path.join(out_dir, fname)

    if not points:
        fig, ax = plt.subplots(figsize=(5, 4), dpi=dpi)
        ax.text(0.5, 0.5, "No data for current filters", ha="center", va="center")
        ax.axis("off")
        fig.savefig(out_path, bbox_inches="tight")
        plt.close(fig)
        return out_path

    arr = np.array(points)
    fig = None
    if arr.shape[1] >= 3 and not np.isnan(arr[:,0]).all() and not np.isnan(arr[:,1]).all():
        # hexbin by location
        lats, lons = arr[:,0], arr[:,1]
        fig, ax = plt.subplots(figsize=(6, 4), dpi=dpi)
        hb = ax.hexbin(lons, lats, gridsize=40, cmap=get_colormap(), mincnt=1)
        ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
        cb = fig.colorbar(hb, ax=ax); cb.set_label("Density")
    else:
        # RSSI histogram fallback
        rssi = arr[:,2] if arr.shape[1] >= 3 else np.array([])
        fig, ax = plt.subplots(figsize=(6, 4), dpi=dpi)
        ax.hist(rssi, bins=30)
        ax.set_xlabel("RSSI (dBm)"); ax.set_ylabel("Count")
        ax.set_title("Signal Distribution")

    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight", dpi=dpi)
    plt.close(fig)
    return out_path
