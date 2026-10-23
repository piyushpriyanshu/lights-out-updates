# The reference lap the app picks for Austin (circuit 9), fetched from OpenF1 exactly as live-ui.js refLap() does.
import json, sys, requests, datetime
B = "https://api.openf1.org/v1/"
def get(ep, q):
    r = requests.get(B + ep + "?" + q, timeout=60); print(ep, q[:90], r.status_code, len(r.content)); 
    return r.json() if r.status_code == 200 else []
now = datetime.datetime.now(datetime.timezone.utc).timestamp()
P = lambda s: datetime.datetime.fromisoformat(s).timestamp()
ss = [s for s in get("sessions", "circuit_key=9") if not s.get("is_cancelled") and P(s["date_end"]) + 35 * 60 < now]
newest = max(ss, key=lambda s: P(s["date_start"]))
rank = lambda s: 3 if s["session_name"] in ("Race", "Sprint") else 2 if "Qualifying" in s["session_name"] or "Shootout" in s["session_name"] else 1
pick = sorted([s for s in ss if s["meeting_key"] == newest["meeting_key"]], key=lambda s: (-rank(s), -P(s["date_start"])))[0]
print("picked", pick["session_key"], pick["session_name"], pick["date_start"])
res = sorted([x for x in get("session_result", "session_key=%d" % pick["session_key"]) if x.get("position")], key=lambda x: x["position"])
drv = res[0]["driver_number"]; print("driver", drv)
laps = sorted([l for l in get("laps", "session_key=%d&driver_number=%d" % (pick["session_key"], drv)) if (l.get("lap_duration") or 0) > 40 and l.get("date_start") and not l.get("is_pit_out_lap")], key=lambda l: l["lap_duration"])
lap = laps[len(laps) // 2] if rank(pick) == 3 and len(laps) > 4 else laps[0]; print("lap", lap["lap_number"], lap["lap_duration"], lap["date_start"])
S = P(lap["date_start"]); E = S + lap["lap_duration"]
iso = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).isoformat().replace("+00:00", "Z")
loc = get("location", "session_key=%d&driver_number=%d&date%%3E=%s&date%%3C=%s" % (pick["session_key"], drv, iso(S - 8), iso(E + 8)))
json.dump({"pick": pick, "driver": drv, "lap": lap, "loc": loc}, open("diag/ref9.json", "w"))
print("location samples", len(loc))
# also: is F1's archive reachable from here, and OpenF1 during the live window?
for u in ["https://livetiming.formula1.com/static/2026/Index.json", B + "sessions?session_key=latest"]:
    try: r = requests.get(u, timeout=20); print("probe", u, r.status_code, r.text[:120].replace("\n", " "))
    except Exception as e: print("probe", u, "ERR", e)
