## Role #4 — Automated report maker
R4-1 Columns: SSID, BSSID (hashed), Enc, Band, Channel, RSSI, Timestamp (+ optional GPS/anchor)  
R4-2 Footer: “MACs pseudonymised; data captured under written permission; see Minutes YYYY-MM-DD.”  
R4-3 Heatmap: Static PNG only (no interactive map in PDF)  
R4-4 Parameters block lists filters/time range  
R4-5 Prototype target: PDF ≤ 4 MB (2–5k rows); export time noted

## Role #2 — Web UI to download files
R2-1 Filenames: `report_<SSID>_<YYYYMMDD-HHMM>_<filters>.pdf`  
R2-2 Downloads view lists name, size, created time  
R2-3 Clicking link opens/downloads successfully  
R2-4 Evidence: screenshot with 2–3 files listed
