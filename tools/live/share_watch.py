"""Live watch of the house share around a car start or heavy load — one line per event.

    HA_TOKEN=... python -I tools/live/share_watch.py <seconds> <raw.log>

Prints setpoint / minimum-SoC / force-state / status / wallbox changes and car power steps
over 500 W; every raw state change goes to <raw.log> with an epoch timestamp, for working
out measured (consumption − car) vs. derived (grid − battery − car) house load afterwards.
Entity ids are Chris's (Victron MQTT c0619ab4e653, go-e via this integration). Run with -I
from a clean directory; stdout is forced to UTF-8 because -I ignores PYTHONIOENCODING.
"""
import asyncio, json, os, sys, time
import websockets
sys.stdout.reconfigure(encoding="utf-8")
P = "sensor.victron_mqtt_c0619ab4e653_"
N = "number.victron_mqtt_c0619ab4e653_system_0_system_"
ENT = {
 P + "grid_0_grid_power": "grid", P + "system_0_system_dc_battery_power": "bat",
 P + "system_0_system_consumption_power_l1": "c1", P + "system_0_system_consumption_power_l2": "c2",
 P + "system_0_system_consumption_power_l3": "c3",
 "sensor.smart_wallbox_charging_wallbox_leistung": "car",
 N + "ac_power_set_point": "SETPOINT", N + "ess_min_soc_limit": "MINSOC",
 "select.smart_wallbox_charging_wallbox_force_state": "FRC",
 "sensor.smart_wallbox_charging_status": "STATUS",
 "sensor.smart_wallbox_charging_wallbox_status": "WALLBOX",
}
async def main(secs, log):
    cur = {}
    last_car = 0.0
    async with websockets.connect("ws://hass.smartpi.home.arpa/api/websocket", max_size=None) as ws:
        await ws.recv()
        await ws.send(json.dumps({"type": "auth", "access_token": os.environ["HA_TOKEN"]}))
        await ws.recv()
        await ws.send(json.dumps({"id": 1, "type": "subscribe_trigger",
            "trigger": {"platform": "state", "entity_id": list(ENT)}}))
        end = time.time() + secs
        f = open(log, "w", encoding="utf-8")
        print("watching", flush=True)
        while time.time() < end:
            try:
                msg = json.loads(await asyncio.wait_for(ws.recv(), end - time.time()))
            except asyncio.TimeoutError:
                break
            if msg.get("type") != "event": continue
            to = msg["event"]["variables"]["trigger"]["to_state"]
            k = ENT[to["entity_id"]]; v = to["state"]
            stamp = time.strftime("%H:%M:%S")
            f.write(f"{time.time():.3f} {k} {v}\n"); f.flush()
            try: cur[k] = float(v)
            except ValueError: cur[k] = v
            out = None
            if k in ("SETPOINT", "MINSOC", "FRC", "WALLBOX"):
                out = f"{stamp} {k} → {v}"
            elif k == "STATUS":
                out = f"{stamp} status: {v}"
            elif k == "car" and isinstance(cur[k], float) and abs(cur[k] - last_car) > 500:
                out = f"{stamp} car {last_car:.0f} → {cur[k]:.0f} W"
                last_car = cur[k]
            elif k in ("c1", "c2", "c3") and all(isinstance(cur.get(x), float) for x in ("c1", "c2", "c3", "car")):
                house = cur["c1"] + cur["c2"] + cur["c3"] - cur["car"]
                derived = cur.get("grid", 0) - cur.get("bat", 0) - cur["car"] if isinstance(cur.get("bat"), float) else None
                if k == "c2":
                    out = f"{stamp} house measured {house:.0f} W | derived {derived:.0f} W" if derived is not None else None
            if out: print(out, flush=True)
asyncio.run(main(float(sys.argv[1]), sys.argv[2]))
