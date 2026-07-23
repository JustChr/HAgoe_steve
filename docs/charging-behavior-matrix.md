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
   (hysteresis + confirmation + 5-min dwell), and the start-confirmation / ride-out machine.
5. The coordinator writes current / phases / start-stop / battery-hold, with the usual write
   shaping (2 s post-write settle, 1 A deadband, redundant writes skipped) — except a
   decisive back-off, which is never made to wait.

## The strategies

| Strategy | Proposes | Active in |
|---|---|---|
| **Solar surplus** | the surplus (0 if below the minimum) — bids the *commitment* signal, charges at the *tracking* one, see below | Smart, Solar only, Solar + minimum |
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

## Two speeds: the knob vs. the switches

Turning the current up or down is cheap and instantly reversible. Starting, stopping and
throwing the 1↔3-phase contactor are not. So the same measured surplus is tracked twice,
and each signal only drives what it suits:

| Signal | Time constants | Drives |
|---|---|---|
| **Tracking** | 12 s up / 5 s down | the **charging current** — a cloud or a switched-on oven reaches the amps in seconds, a clearing sky is used while it lasts |
| **Commitment** | 120 s up / 20 s down | **whether to charge at all** and **how many phases** — on top of the confirmation, ride-out and dwell timers below |

So a passing cloud visibly moves the amps and moves nothing else; only a surplus change
that *persists* is allowed to stop the session or move the contactor. The status reason
always quotes whichever number it acted on, so the surplus shown and the amps shown agree.

Two properties make the fast loop safe rather than twitchy: above the reserve line the
surplus identity (`car draw + battery charge − grid`) is invariant to the car's own draw,
so raising the current doesn't change the signal it was derived from; and the 2 s
post-write settle keeps us from reacting to our own last move.

**How fast is fast enough?** The tracking time constants are set by the *sample rate*, not
by taste. An EMA's output noise scales with `dt/τ`, and the loop re-evaluates about every
1.5 s, so a 5 s τ still averages ~3 samples — quieter than a 12 s τ would be on a meter
that only reported every 5 s. What stops us going lower is not noise but **real** short
transients: at τ=5 s a 2-second compressor or kettle blip moves the current about 2 A and
back, at τ=2 s it moves ~3.4 A. Beyond that, two hard limits make a faster loop pointless
anyway — a car may take several seconds to follow a changed pilot signal, and the 1 A write
deadband is ~690 W at 3φ, so sub-deadband wobbles are never written at any speed.

---

## The home battery (read this once)

One slider — **"Keep home battery above X %"** — plus one principle:

> **The battery may buffer solar charging, but deliberate grid charging never drains it.**

```
100 % ┤
      │   AT/ABOVE the line — the battery is a fluctuation buffer:
      │   • the car follows the surplus closely (tracking signal)
      │   • the battery still bridges the seconds the car needs to follow:
      │     the discharge deduction builds slowly, and is released quickly
      │     again once the dip is over so it stops holding the amps down
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
surplus ≥ min ──────► confirm ~3 min ──────► CHARGING (amps track the surplus)
   (commitment signal)                             │
                                     surplus < min │ (cloud front, evening)
                                     (commitment)  ▼
                                        RIDE-OUT ~5 min, amps still
                                        following the live surplus
                                        (battery covers above the line,
                                         briefly grid below it)
                                          │                │
                              surplus back│                │ still gone
                                          ▼                ▼
                                       CHARGING          STOP (clean)
```

The ride-out is a decision to *not stop yet*, not an instruction to sit at the minimum: if
the surplus recovers inside the window the amps go straight back up with it, and only the
stop keeps waiting on the calm signal.

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
  surplus clears the 3φ minimum *plus 500 W of headroom* (~4.6 kW); back down below what 1φ
  can deliver at max current. The margin is one-sided on purpose — widening the band
  downwards would mean holding 3φ (and its higher minimum) on a surplus a single phase
  could carry alone. Thresholds evaluate both candidate configurations, not the currently
  active one.
* Three things must agree before the contactor moves: it reads the **commitment** signal,
  the crossing must **hold for 2 minutes**, and at least **5 minutes** must have passed
  since the last switch. A spike or a momentary dip re-arms the 2-minute window from
  scratch, so it costs nothing.
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
| `SURPLUS_TRACK_RISE_TAU_S` | 12 s | **tracking** (the amps) — surplus **rises** |
| `SURPLUS_TRACK_DROP_TAU_S` | 5 s | **tracking** (the amps) — surplus **falls** |
| `SURPLUS_SMOOTH_WINDOW_S` | 120 s | **commitment** (start/stop, phases) — surplus **rises** |
| `SURPLUS_DROP_TAU_S` | 20 s | **commitment** (start/stop, phases) — surplus **falls** |
| `BATTERY_DISCHARGE_TOLERANCE_W` | 300 W | buffer discharge allowed before the ease-off |
| `BATTERY_DISCHARGE_GRACE_S` | 180 s | how long it may exceed the tolerance |
| `BATTERY_DISCHARGE_ATTACK_S` | 120 s | how slowly the discharge deduction builds (the bridging tolerance) |
| `BATTERY_DISCHARGE_RELEASE_S` | 40 s | how quickly it is released once the dip is over |
| `START_CONFIRM_S` | 180 s | surplus must hold ≥ min before a solar start |
| `STOP_RIDE_OUT_S` | 300 s | dip ridden out before a stop |
| `PHASE_DWELL_S` | 300 s | minimum time between 1↔3 phase switches |
| `PHASE_CONFIRM_S` | 120 s | a threshold crossing must hold this long first |
| `PHASE_UP_MARGIN_W` | 500 W | headroom demanded before climbing to 3φ |
| `MIN_UPDATE_INTERVAL_S` | 2 s | post-write settle before commanding again |
| `FAST_BACKOFF_DELTA_A` | 2 A | a drop this large skips that settle |
| `MIN_WRITE_DELTA_A` | 1 A | write deadband (~690 W at 3φ) |
