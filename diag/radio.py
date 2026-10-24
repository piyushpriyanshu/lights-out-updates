# Are F1's team radio clips still public? Takes today's FP1/FP2 clip addresses from OpenF1 and asks F1's server for them.
import requests, json
B = "https://api.openf1.org/v1/"
for sk in (11389, 11390):
    r = requests.get(B + "team_radio?session_key=%d" % sk, timeout=60); print("openf1 team_radio", sk, r.status_code, len(r.content))
    clips = r.json() if r.status_code == 200 else []
    print(" clips", len(clips), clips[:1])
    for c in clips[:3]:
        u = c["recording_url"]
        for ua in ("BestHTTP", "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/141 Mobile Safari/537.36"):
            h = requests.get(u, headers={"User-Agent": ua}, timeout=30, stream=True); print(" ", h.status_code, h.headers.get("content-type"), h.headers.get("content-length"), ua[:10], u[-60:]); h.close()
for u in ["https://livetiming.formula1.com/static/2026/Index.json", "https://livetiming.formula1.com/static/2026/2026-10-25_United_States_Grand_Prix/2026-10-23_Practice_1/Index.json"]:
    h = requests.get(u, timeout=30); print("probe", h.status_code, h.headers.get("content-type"), u[-70:], h.text[:80].replace("\n", " "))
