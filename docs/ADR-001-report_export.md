# ADR-001 — Report export approach (static PNG in PDF)

## Context
Our report must show (a) table of evidence [SSID, BSSID (hashed), enc, band, channel, RSSI, timestamp], (b) static heatmap image, (c) parameters/filters used, (d) audit footer.

## Options
A) Programmatic PDF (Python PDF libs): deterministic layout, reliable image placement; slower to style.  
B) HTML/CSS → PDF (print a page): fast to iterate; interactive maps (Folium/JS) don’t render to PDF, so we must export PNG first.

## Decision (MVP)
Use **static PNG heatmaps embedded in a deterministic PDF** (or a printed static HTML) for auditability and portability. Interactive maps remain for the web demo.

## Consequences
- Export pipeline is reproducible across machines.
- We keep a small, fixed footer: “MACs pseudonymised; data captured under written permission; see Minutes 2025-09-01.”
