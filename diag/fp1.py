# Waits until OpenF1's free data reopens after US GP FP1, then saves the session and the reference laps the app uses.
import json, time, os, requests, datetime
B = "https://api.openf1.org/v1/"; os.makedirs("diag/fp1", exist_ok=True)
def get(ep, q, tries=40):
    for k in range(tries):
        r = requests.get(B + ep + "?" + q, timeout=90)
        if r.status_code == 200: return r.json()
        if r.status_code == 404: return []
        print(ep, q[:80], "status", r.status_code, r.text[:100].replace("\n", " "), flush=True); time.sleep(30)
    return None
P = lambda s: datetime.datetime.fromisoformat(s).timestamp()
iso = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).isoformat().replace("+00:00", "Z")
ss = get("sessions", "circuit_key=9", 50) or []
json.dump(ss, open("diag/fp1/sessions9.json", "w")); print("sessions at Austin", len(ss), flush=True)
fp1 = [s for s in ss if s["year"] == 2026 and s["session_name"] == "Practice 1"]
print("FP1", fp1[:1], flush=True)
def save_ref(s, tag, race):
    res = sorted([x for x in (get("session_result", "session_key=%d" % s["session_key"]) or []) if x.get("position")], key=lambda x: x["position"])
    if not res: print(tag, "no result"); return
    drv = res[0]["driver_number"]
    laps = sorted([l for l in (get("laps", "session_key=%d&driver_number=%d" % (s["session_key"], drv)) or []) if (l.get("lap_duration") or 0) > 40 and l.get("date_start") and not l.get("is_pit_out_lap")], key=lambda l: l["lap_duration"])
    lap = laps[len(laps) // 2] if race and len(laps) > 4 else laps[0]
    S = P(lap["date_start"]); E = S + lap["lap_duration"]
    loc = get("location", "session_key=%d&driver_number=%d&date%%3E=%s&date%%3C=%s" % (s["session_key"], drv, iso(S - 8), iso(E + 8))) or []
    json.dump({"session": s, "driver": drv, "lap": lap, "loc": loc}, open("diag/fp1/ref-%s.json" % tag, "w")); print(tag, "driver", drv, "lap", lap["lap_number"], lap["lap_duration"], "samples", len(loc), flush=True)
if fp1:
    k = fp1[0]["session_key"]
    for ep in ["drivers", "laps", "position", "stints", "pit", "race_control", "weather", "session_result"]:
        d = get(ep, "session_key=%d" % k); json.dump(d, open("diag/fp1/%s.json" % ep, "w")); print(ep, len(d or []), flush=True)
    save_ref(fp1[0], "fp1", False)
r25 = [s for s in ss if s["year"] == 2025 and s["session_name"] == "Race"]
if r25: save_ref(r25[0], "race2025", True)
