# Charging behavior — the contract

What the brain does in every situation. Derived from the regulation engine
([`engine.py`](../custom_components/goe_steve/engine.py), `decide()`), which implements a
**strategies + arbiter** design (v3).

Defaults (all runtime-adjustable): **6 A min / 16 A max**, cheap grid **≤ 0.15 /kWh**,
home-battery **reserve line 100 %**.

---

## How a decision is made (every ~30 s, plus on every sensor change)

1. **Gates** — smart control on? car connected? required inputs fresh? Otherwise the brain
   releases the charger entirely (no writes).
2. **Every enabled strategy proposes a charging power** (see the table below).
3. **The arbiter takes the highest proposal.** Grid strategies win ties, so the battery-hold
   stays engaged when grid and solar could deliver the same.
4. **Shared constraints** shape the winner: the battery policy, 1↔3-phase resolution
   (hysteresis + 5-min dwell), and the start-confirmation / ride-out machine.
5. The coordinator writes current / phases / start-stop / battery-hold, with the usual write
   shaping (5 s settle, 1 A deadband, redundant writes skipped).

## The strategies

| Strategy | Proposes | Active in |
|---|---|---|
| **Solar surplus** | the surplus, eased up slowly but tracked down fast (0 if below the minimum) | Smart, Solar only, Solar + minimum |
| **Cheap grid** | full power while `price ≤ cheap threshold` | Smart |
| **Departure plan** | full power during the cheapest forecast slots that cover the **remaining** energy (target − delivered) by departure — **hard guarantee** | Smart |
| **Minimum floor** | the minimum current, always | Solar + minimum |
| **Full power** | maximum, unconditionally | Fast |

## Modes are presets

| Mode | Strategies | One line |
|---|---|---|
| **Smart** | surplus + cheap grid + departure plan | Solar first, cheap grid opportunistically, target guaranteed by departure. |
| **Solar only** | surplus | No sun, no charge. |
| **Solar + minimum** | surplus + floor | Solar surplus, but never below the minimum current (tops up from grid). |
| **Fast** | full power | Full power now, no questions. |
| **Manual** | — (bypasses the arbiter) | You drive: start/stop, current, phases from the card. |

Without a PV sensor, Smart degrades gracefully to price-only charging (the surplus strategy
simply proposes 0). Old modes map automatically: *Solar + cheap grid*, *Price-optimized* and
*Combined* → **Smart**; *Off* → **Manual**.

---

## The home battery (read this once)

One slider — **"Keep home battery above X %"** — plus one principle:

> **The battery may buffer solar charging, but deliberate grid charging never drains it.**

```
100 % ┤
      │   AT/ABOVE the line — the battery is a fluctuation buffer:
      │   • the car follows the surplus — eased up slowly, tracked down fast
      │   • short dips/spikes (clouds) are bridged by the battery — the car
      │     current stays calm instead of chasing every wobble
      │   • sustained discharge into the car (> 300 W for > 3 min) is corrected:
      │     the car eases off until solar genuinely covers it again
  X % ┤◄══ your reserve line ══════════════════════════════════════════
      │   BELOW the line — the battery comes first:
      │   • all solar fills the battery; the car gets only genuine excess
      │     (export the battery can't absorb), with zero discharge tolerance
      │   • grid charging (cheap hours, plan, floor, Fast) still runs
  0 % ┤
```

**Whenever a grid strategy wins** (cheap hour, departure plan, minimum floor, Fast — and
Manual whenever the requested power exceeds the surplus), the brain turns the mapped
**battery-hold switch ON** so grid power charges the car, never the battery. It is released
as soon as solar carries the session again or the brain lets go. As a fallback when no hold
switch is mapped, the current is trimmed by whatever the battery discharges.

With the battery SoC unknown, the brain is conservative: genuine solar excess only.

---

## Start/stop: "ride out, then stop"

Solar charging transitions are deliberate, not flappy:

```
surplus ≥ min ──────► confirm ~3 min ──────► CHARGING (up slow, down fast)
                                                   │
                                     surplus < min │ (cloud front, evening)
                                                   ▼
                                        RIDE-OUT ~5 min at min current
                                        (battery covers above the line,
                                         briefly grid below it)
                                          │                │
                              surplus back│                │ still gone
                                          ▼                ▼
                                       CHARGING          STOP (clean)
```

Grid strategies are exempt in both directions: a cheap hour / plan slot / Fast starts
immediately and stops immediately at its boundary — no ride-out on expensive grid.

## The departure plan (Smart)

* Set **target energy** and **departure**; 0 kWh disables planning.
* Remaining = target − energy delivered this session (anchored at plug-in), so the plan
  shrinks as the car fills and stops at the target. Solar surplus and cheap hours still
  charge beyond it — the target is a floor, not a cap.
* Slot capacity uses the phases charging can actually use (respects auto-phase off).
* **Hard guarantee**: the plan books the least-expensive remaining slots until the remaining
  energy is covered, whether or not they beat the cheap threshold. If the remaining time only
  just covers the remaining energy at full power, it charges regardless of the forecast.

## Phases (with auto-phase on)

* Solar charging prefers **1φ** (usable from ~1.4 kW) and climbs to **3φ** only once the
  surplus sustains the 3φ minimum (~4.1 kW); back down below what 1φ can deliver at max
  current. 5-minute dwell between switches. Thresholds evaluate both candidate
  configurations, not the currently active one.
* Grid charging always runs at the full phase count.
* With auto-phase off the brain never touches the phase switch (except Manual, where you
  pick the phases explicitly).

## Status reasons

Every decision carries a plain-language reason (localized on the card): what's charging and
why (`Solar surplus 5,2 kW → 7,5 A`, `Planned cheap hour…`), what it's waiting for
(`confirming before start`, `battery below reserve`, `waiting for a planned cheap hour`), or
what just finished (`Departure target reached`).

## Tunables (constants in [`const.py`](../custom_components/goe_steve/const.py))

| Constant | Default | Meaning |
|---|---|---|
| `SURPLUS_SMOOTH_WINDOW_S` | 120 s | slow time constant when the surplus **rises** |
| `SURPLUS_DROP_TAU_S` | 20 s | fast time constant when the surplus **falls** |
| `BATTERY_DISCHARGE_TOLERANCE_W` | 300 W | buffer discharge allowed before the ease-off |
| `BATTERY_DISCHARGE_GRACE_S` | 180 s | how long it may exceed the tolerance |
| `START_CONFIRM_S` | 180 s | surplus must hold ≥ min before a solar start |
| `STOP_RIDE_OUT_S` | 300 s | dip ridden out at min current before a stop |
| `PHASE_DWELL_S` | 300 s | minimum time between 1↔3 phase switches |
