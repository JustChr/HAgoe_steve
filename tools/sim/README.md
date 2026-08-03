# Peak-protection simulation harness

Drives the **real** `engine.py` against a model house, so charging behaviour can be played
through before it reaches a wallbox. Nothing here ships with the integration — it is a
development tool, and CI does not run it (`pytest tests/ -q` is scoped to `tests/`).

## Why a harness and not more unit tests

Unit tests answer *"given this snapshot, is the decision right?"*. They cannot answer
*"does the guard settle, or does it oscillate?"* — because that depends on the world
reacting to what the engine just did.

So this closes the loop: the grid reading the engine sees on tick N is produced by the
house model reacting to the decision it made on tick N-1. Open-loop, every stability
finding is fiction.

The house model is one equation. On a Victron ESS the grid setpoint is a *total import
target*, so the battery makes up the difference between the load and that target, bounded
by its minimum SoC and its power limits. That single rule reproduces both ordinary
self-consumption and the guard's hard-tier `setpoint → 0`.

## Files

| | |
|---|---|
| `peak_sim.py` | The loop: `House` (ESS model) + `run()` + weather/load profile builders |
| `scenarios.py` | 20 single-event scenarios — tiers, dwell, degraded windows, month rollover, hands-off modes |
| `winter.py` / `winter_scenarios.py` | Multi-day runs at 30 s ticks: does the battery's *energy* last a December week? |
| `real_ab.py` | A/B a change against the real measured baseline, prices and battery |
| `peak15.py` | 15 winter days vs a 4 kW ceiling, recorded per billing quarter-hour |
| `build_chart.py` | Renders that run into a self-contained HTML readout |
| `ha_ws.py` / `pull_winter.py` | Pull long-term statistics out of Home Assistant |

```bash
python tools/sim/scenarios.py            # all 20
python tools/sim/scenarios.py 14         # just one
python tools/sim/winter_scenarios.py 2   # a December week
python tools/sim/real_ab.py              # needs the snapshots below
python tools/sim/peak15.py               # 15 days × 3 variants → peak15_run.json
python tools/sim/build_chart.py          # → peak15_chart.html (git-ignored: real data)
```

## What `peak15.py` is for

`real_ab.py` answers "is this change better?". `peak15.py` answers the question a
*capacity tariff* asks — "what was the worst quarter-hour, and could anything have
prevented it?" — by running the same fortnight four times: protection off, the
integration as it ships, protection forced to defend the line all month
(`peak_follow_month=False`), and **ceiling-fill** — defend all month *and* keep the
battery stocked by importing on every hour with headroom under the ceiling.

Ceiling-fill is the one that works: **5 quarter-hours out of 1440** over 4 kW, against
111 as shipped, for about €1.50/day more and no loss of car energy. It is
`peak_follow_month=False` plus `peak_ready_soc` plus a deeper shaving floor — the first
is a switch that already existed, the second was added because of these runs.

The three levers the runs produced are now in the engine (`peak_ready_soc`, `stock_up` /
`stock_up_target_soc`, and the grid-charge resume band), so the harness drives the real
fields rather than faking them. That matters: an earlier version emulated ceiling-fill by
setting `cheap_price` absurdly high, which also unleashed the *car's* cheap-grid strategy
and flattered the result. Keep the wallbox's price gate fixed across variants or the
comparison is not about the battery.

What the runs established, mostly by getting them wrong first:

- **Calibrate the heat pump on daily energy**, not on how the curve looks. The house
  totals are anchored to the measured 36.4 kWh/day.
- **Don't let a modelled load cycle in lockstep with the billing window.** A clean
  1800 s compressor cycle aliases against the 15-minute quarter-hour and makes every
  other slot read high — a peak the house never had. Both the heat pump and the sauna
  therefore use a wandering period.
- **A pre-fill has two halves.** Filling the battery before a known event and then
  letting it serve the ordinary afternoon load donates the whole stock to a few hours
  the grid could have carried for free. Raise the reserve as well, or don't bother.
- **`apply_grid_charge` had no hysteresis** — fixed, with the band *measured* rather
  than guessed. Against a 100 % target the fortnight imported 864 kWh with no band,
  776 at 2 %, 771 at 5 %, 769 at 10 %: 2 % captures 88 of the 95 kWh available and is
  the widest band that costs nothing in worst quarter-hour or breach count. Sweep the
  knob you are about to hard-code; the obvious round number was 2.5× too wide.
- **Charge the battery efficiency.** `House(charge_eff=…)` defaults to 1.0 so the older
  scenarios are untouched; anything that cycles the pack hard must set it (peak15 uses
  0.90) or its conclusions are free energy.

## Getting the data

The `*.json` snapshots are **git-ignored on purpose** — they are real household
consumption and a full entity dump. Regenerate them against your own instance:

```bash
export HA_URL=http://your-ha.local:8123
export HA_TOKEN=...        # Profile → Security → Long-lived access tokens
python tools/sim/pull_winter.py
```

`real_ab.py` also wants `price_curve.json` (mean EPEX price per hour of day) — see the
inline comment there for the query.

**Resolution matters.** Home Assistant keeps hourly statistics forever but 5-minute
statistics only ~10 days. A past quarter-hour peak therefore cannot be reconstructed, only
bracketed: the hourly *mean* is a hard lower bound on the worst quarter-hour inside that
hour, the hourly *max* an upper bound. Use the integration's own `monatsspitze` /
`diese_viertelstunde` sensors for the real record going forward.

## Rules learned the hard way

- **Do not invent system specs.** A run against a guessed 10 kWh battery and 4.5 kW
  inverter produced confident numbers for a house with 30.5 kWh and 10.2 kW. The mechanics
  survived; every quantity had to be retracted. Measure first, and list anything you had to
  assume before drawing conclusions from it.
- **Split steerable from non-steerable load before quantifying anything.** "Battery energy
  needed to shave the profile as it ran" is the wrong question for a load you can simply
  move to another hour.
- **Never credit a controllable load in a headroom calculation.** Crediting home-battery
  discharge to the charge ceiling made it self-referential (charge more → battery covers
  more → ceiling rises) and walked the phase contactor 36 times in four days.
- **Calibrate load models against real daily kWh** before trusting them. The first
  heat-pump curve here drew 241 kWh/day.
