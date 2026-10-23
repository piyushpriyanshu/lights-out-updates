# Records the public F1 live timing feed (no sign-in) for a few minutes, exactly as the Lights Out app subscribes,
# and summarises what arrives: topics, how often, and how old Position.z / CarData.z data is when it arrives.
import json, time, sys, base64, zlib, datetime, requests, websocket
DUR = int(sys.argv[1]) if len(sys.argv) > 1 else 240
H = {"User-Agent": "BestHTTP"}
o = requests.options("https://livetiming.formula1.com/signalrcore/negotiate", headers=H, timeout=15)
cookie = "; ".join(f"{k}={v}" for k, v in o.cookies.items() if k.startswith("AWSALB"))
r = requests.post("https://livetiming.formula1.com/signalrcore/negotiate?negotiateVersion=1", headers=dict(H, Cookie=cookie), timeout=15)
print("negotiate", r.status_code, r.text[:200]); tok = r.json()["connectionToken"]
ws = websocket.create_connection("wss://livetiming.formula1.com/signalrcore?id=" + requests.utils.quote(tok, safe=""), header=["User-Agent: BestHTTP", "Cookie: " + cookie], timeout=20)
RS = "\x1e"; ws.send('{"protocol":"json","version":1}' + RS)
topics = ["Heartbeat", "ExtrapolatedClock", "TimingStats", "TimingAppData", "WeatherData", "TrackStatus", "SessionStatus", "DriverList", "RaceControlMessages", "SessionInfo", "SessionData", "LapCount", "TimingData", "TopThree", "Position.z", "TeamRadio", "CarData.z"]
out = open("diag/feed.jsonl", "w"); t0 = time.time(); subscribed = False; buf = ""
def utc(s): return datetime.datetime.fromisoformat(s.replace("Z", "+00:00") if "+" in s[10:] or s.endswith("Z") else s + "+00:00").timestamp()
stats = {}; lags = {"Position.z": [], "CarData.z": []}; hb = []
while time.time() - t0 < DUR:
    try: data = ws.recv()
    except websocket.WebSocketTimeoutException: continue
    rx = time.time(); buf += data if isinstance(data, str) else data.decode()
    while RS in buf:
        one, buf = buf.split(RS, 1)
        if not one.strip(): continue
        if not subscribed:
            subscribed = True; ws.send(json.dumps({"type": 1, "invocationId": "1", "target": "Subscribe", "arguments": [topics]}) + RS); continue
        out.write(json.dumps({"rx": rx, "m": one}) + "\n")
        m = json.loads(one)
        if m.get("type") == 3:
            res = m.get("result") or {}; print("snapshot topics:", sorted(res.keys()), "error:", m.get("error"))
            for k in ("Position.z", "CarData.z"):
                if k in res:
                    try:
                        d = json.loads(zlib.decompress(base64.b64decode(res[k]), -15)); arr = d.get("Position") or d.get("Entries") or []
                        ts = arr[-1].get("Timestamp") or arr[-1].get("Utc") if arr else None; print(" snapshot", k, "last timestamp", ts, "age s", round(rx - utc(ts), 1) if ts else None)
                    except Exception as e: print(" snapshot", k, "undecodable", e)
            continue
        if m.get("type") != 1: continue
        tp, d = m["arguments"][0], m["arguments"][1]; stats[tp] = stats.get(tp, 0) + 1
        if tp == "Heartbeat": hb.append((rx, d.get("Utc")))
        if tp in lags:
            try:
                z = json.loads(zlib.decompress(base64.b64decode(d), -15)); arr = z.get("Position") or z.get("Entries") or []
                ts = arr[-1].get("Timestamp") or arr[-1].get("Utc"); lags[tp].append(round(rx - utc(ts), 2))
            except Exception as e: lags[tp].append(str(e)[:40])
ws.close(); out.close()
print("seconds", DUR, "messages per topic:", json.dumps(stats, sort_keys=True))
for k, v in lags.items(): print(k, "count", len(v), "age on arrival (s) first/median/last:", v[:3], sorted([x for x in v if isinstance(x, float)])[len(v)//2] if v else None, v[-3:])
print("heartbeats", hb[:2], "...", hb[-1:] if hb else None)
