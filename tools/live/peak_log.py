"""Log the live peak-protection loop every 5 s, one line per change.

Reads the integration's own sensors over Home Assistant's REST API and appends a line
whenever anything moves: grid / battery / car / house / SoC / PV, the quarter-hour
projection and tier, the ESS setpoint and minimum SoC, the charger's force state, and
both reason lines. Used for the first live peak test (2026-11-06).

    export HA_URL=http://your-ha.local:8123  HA_TOKEN=...
    python tools/live/peak_log.py peak.log             # runs until stopped
    python tools/live/peak_log.py peak.log --changes   # tail it: tier/levers only

Entity ids follow the German-named live instance (``smart_wallbox_charging_*``) and
its Victron setpoint; adjust ``SETPOINT`` for yours.
"""

from __future__ import annotations

import datetime
import json
import os
import sys
import time
import urllib.request

BASE = os.environ.get("HA_URL", "http://hass.smartpi.home.arpa").rstrip("/") + "/api/states/"
HEADERS = {"Authorization": "Bearer " + os.environ.get("HA_TOKEN", "")}
P = "sensor.smart_wallbox_charging_"
SETPOINT = "number.victron_mqtt_c0619ab4e653_system_0_system_ac_power_set_point"
# What the ESS actually holds, beside what the engine asked for: since v5.9 they differ
# by the cap at the battery's charge and the entity's 5 % step.
MIN_SOC = "number.victron_mqtt_c0619ab4e653_system_0_system_ess_min_soc_limit"


def get(entity: str) -> dict:
    try:
        req = urllib.request.Request(BASE + entity, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.load(r)
    except Exception:  # noqa: BLE001 - a dropped poll is a gap, not a crash
        return {"state": "ERR", "attributes": {}}


def log(path: str) -> None:
    out = open(path, "a", buffering=1, encoding="utf-8")
    out.write("time     | grid bat car house soc pv | projected tier | setpoint minsoc | frc  status // peak status\n")
    last = None
    while True:
        flow = get(P + "energiefluss")["attributes"]
        qh = get(P + "diese_viertelstunde")["attributes"]
        peak = get(P + "status_lastspitzenschutz")
        row = (
            *(flow.get(k, "?") for k in ("grid_w", "battery_w", "car_w", "house_w", "battery_soc", "pv_w")),
            qh.get("projected_w"), qh.get("tier"),
            get(SETPOINT)["state"],
            f"{peak['attributes'].get('battery_min_soc')}/{get(MIN_SOC)['state']}"
            f" {'REFILL' if peak['attributes'].get('battery_refilling') else '-'}",
            get("select.smart_wallbox_charging_wallbox_force_state")["state"],
            get(P + "status")["state"], peak["state"],
        )
        if row != last:
            stamp = datetime.datetime.now().strftime("%H:%M:%S")
            out.write(f"{stamp} | {' '.join(map(str, row[:6]))} | {row[6]} {row[7]} | "
                      f"{row[8]} {row[9]} | {row[10]}  {row[11]} // {row[12]}\n")
            last = row
        time.sleep(5)


def changes(path: str) -> None:
    """Follow the log, printing only lines where tier, levers or charger state change."""
    f = open(path, encoding="utf-8", errors="replace")
    f.seek(0, 2)
    prev = None
    while True:
        line = f.readline()
        if not line:
            time.sleep(1)
            continue
        p = line.split(" | ")
        if len(p) < 5:
            continue
        key = (p[2].split()[-1], p[3], p[4].split(" // ")[0].split()[0])
        if key != prev or "ERR" in line:
            print(line.rstrip(), flush=True)
        prev = key


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) > 2 and sys.argv[2] == "--changes":
        changes(sys.argv[1])
    else:
        log(sys.argv[1])
