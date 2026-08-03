# Charging behavior — the contract

What the brain does in every situation. Derived from the regulation engine
([`engine.py`](../custom_components/goe_steve/engine.py), `decide()`), which implements a
**strategies + arbiter** design (v3).

Defaults (all runtime-adjustable): **6 A min / 16 A max**, cheap grid **≤ 0.15 /kWh**,
home-battery **reserve line 100 %**.

**Minimum current** is the *Solar + minimum* setting and nothing else: it is what that mode
tops up to from the grid, and the card offers it only there. Raising it never affects any
other mode — everywhere else a charge bottoms out at the EV's own floor of **6 A**.

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
| **Solar surplus** | the surplus (0 if below the mode's floor: 6 A, or the minimum current in Solar + minimum) — bids the *commitment* signal, charges at the *tracking* one, see below | Smart, Solar only, Solar + minimum |
| **Cheap grid** | full power while `price ≤ cheap threshold` | Smart |
| **Departure plan** | full power during the cheapest forecast slots that cover the **remaining** energy (target − delivered) by departure — **hard guarantee** | Smart |
| **Minimum floor** | the **minimum current** setting, always | Solar + minimum |
| **Full power** | maximum, unconditionally | Fast |

**Peak protection is not in this table, and that is deliberate.** The arbiter takes the
*highest* proposal, so a strategy that wants to charge *less* has no way to say so. It is a
**ceiling applied after the arbiter** instead — which is also why it covers every mode
including Manual and Fast, and every branch including "no car connected". See below.

## Modes are presets

| Mode | Strategies | One line |
|---|---|---|
| **Smart** | surplus + cheap grid + departure plan | Solar first, cheap grid opportunistically, target guaranteed by departure. |
| **Solar only** | surplus | No sun, no charge. Starts as soon as the surplus carries 6 A. |
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
anyway — a car may take several seconds to follow a changed pilot signal, and `amp` is
integer amps, so the smallest step that can reach the charger is 1 A (~690 W at 3φ, 230 W
at 1φ) however fast the loop runs. The charger itself is *not* a limit: it takes more than
one write per second without complaint.

---

## The home battery (read this once)

One slider — **"Keep home battery above X %"** — plus one principle:

> **The battery may buffer solar charging, but deliberate grid charging never drains it.**

```
100 % ┤
      │   COMFORTABLY ABOVE the line (from halfway between it and 100 %):
      │   • the charging current rounds UP to the next whole amp instead of
      │     down, so the last few hundred watts of surplus go into the car
      │     and come out of the battery, instead of being exported
      │   ↕ ┄┄ halfway mark ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
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

### Which side of the surplus do we land on?

The charger takes **whole amps**, so a surplus never divides evenly: one amp is ~230 W on a
single phase and ~690 W on three. The charge therefore lands either just *below* the surplus
(the remainder is exported) or just *above* it (the remainder comes out of the home battery),
and the brain picks the side deliberately:

| Home battery | Rounding | Effect |
|---|---|---|
| below the reserve, or SoC unknown | down | the battery comes first, nothing is borrowed |
| above the reserve, below the halfway mark | down | up to one amp step is exported |
| **at/above the halfway mark** (e.g. reserve 80 % → from 90 %) | **up** | up to one amp step is borrowed from a battery that is nearly full anyway |
| **reserve set to 100 %** | down, always | "protect it unconditionally" is taken literally |

Leaving the generous zone takes 3 points more SoC than entering it — rounding up nudges the
SoC back down across the very threshold that enabled it, and the direction should not
chatter. The borrowed watts are visible in the status reason ("*the last 520 W come from the
home battery instead of being exported*") and, being our own doing, they do not count toward
the sustained-discharge ease-off above.

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

**Don't want to wait?** While the ~3-minute confirmation runs, the card's countdown chip is a
button ("Start now"), backed by a **Start now** button entity that is available exactly while
that wait is running. It skips the *waiting* only — the surplus still has to carry the
minimum current, so it can never start a charge the sun can't pay for.

Grid strategies are exempt in both directions: a cheap hour / plan slot / Fast starts
immediately and stops immediately at its boundary — no ride-out on expensive grid.

### A pause is held, not just announced

Pausing is the charger's force-state (`frc = Off`), never a current of zero — the requested
current floors at 6 A and so cannot stop anything on its own.

That force-state is **re-asserted, not set once**. The charger can move it without telling
us — verified: **unplugging a car clears `frc` to Neutral** a few seconds later, whatever the
brain wanted (see [mqtt-direct-concept.md](mqtt-direct-concept.md)); the go-e app can change
it too. So the brain checks what the charger *reports* alongside what it last wrote, and puts
its value back (within ~10 s) whenever the two disagree.

Without that, a pause quietly stops pausing. Swapping cars is the ordinary way to hit it: the
brain holds car A off, you unplug it, the charger drops the hold, you plug in car B — and
because the brain's decision never changed ("still don't charge"), it never writes again. The
Status sensor goes on reading *waiting for the home battery* at 0 A while the car charges at
the minimum, and nothing in the UI contradicts it.

Two consequences worth knowing:

* Setting **Force state** by hand is authoritative only while the brain isn't controlling the
  charger. With Smart control on, the brain owns it and will take it back. To drive the box
  yourself, use Manual mode; to hand it over entirely, turn Smart control off.
* While paused, the requested current is parked at the minimum. It changes nothing on its
  own — the force-state is what holds the car — but if the charger is ever released or
  cleared behind our back, an unplanned session starts at 6 A rather than at whatever the
  previous car was drawing.

The same read-back covers the phase mode (`psm`). It does **not** cover the requested current,
which is written under its own deadband and rate limit while charging.

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
why (`Solar surplus 5200 W → 8 A`, `Planned cheap hour…`), what it's waiting for
(`confirming before start`, `battery below reserve`, `waiting for a planned cheap hour`), or
what just finished (`Departure target reached`).

Peak protection has its own second line (the *Peak status* sensor) so the two never compete
for the one the card shows, but it will not let the first one lie about the charge:

* when it **trims** the car, the reason keeps its explanation and only the number changes —
  the car really is fast-charging, just at 11 A instead of 16;
* when it **pauses** the car, it takes the line over. "Fast charging at 16 A" beside a car
  standing at 0 A is wrong however well the peak line explains why.

---

## Peak protection — the capacity tariff (from 2027)

From January 2027 Austrian grid operators bill households not only on kWh but on the
**highest average grid import over a fixed clock quarter-hour** (:00/:15/:30/:45) in the
month. One unlucky 15 minutes sets a charge that stands until the month ends.

**Off by default.** With it off, the brain behaves exactly as it did before — one early
return, nothing written anywhere. The *measurement* still runs, so you can watch your peaks
for a month before deciding to let anything act on them.

**This is a household layer, not a wallbox one.** A sauna or a heat pump sets the peak
whether or not a car is plugged in, so it also runs on the "no car connected" branch, and its
levers include the home battery. It is the one thing here governed by its own switch rather
than by *Smart control*: a demand charge is money either way.

### How the limit is worked out

```
window   = now floored to :00/:15/:30/:45
elapsed  = now − window            remaining = 900 s − elapsed
imported = Σ max(0, grid) · dt     (the last reading held until the next one)

average   = imported · 3600 / elapsed        ← what the window has drawn
projected = (imported · 3600 + grid · remaining) / 900   ← where it lands
allowed   = (target · 900 − imported · 3600) / max(remaining, 60)
```

The **projection** is what the three limits are compared against, so the brain reacts to
where the quarter-hour is heading rather than to a spike. The throttle needs no ramp logic:
`allowed` tightens smoothly on its own as the window fills, and a fresh quarter-hour is a
fresh budget, so it relaxes at every boundary without being told to.

Only **import** counts — exporting 5 kW does not buy back a kilowatt of peak. The last
minute is deliberately conservative (the divisor floors at 60 s), because otherwise the
budget would diverge as the window closes and the amps would leap at every boundary.

### The three tiers

| Tier | Engages | What happens |
|---|---|---|
| **Soft** (3.3 kW) | projection over it for **120 s** | The wallbox eases back to whatever the budget leaves, down to 6 A. It never pauses. |
| **Target** (3.7 kW) | — | Not a tier: the number the budget aims at. |
| **Hard** (3.9 kW) | projection over it, **immediately** | Setpoint → 0 W, and the car is paused outright if the budget can't carry even 6 A. |

The kW figures above are the ones you set. All three are compared in their **effective**
form — see the month-peak allowance below, which can lift them. The soft line travels the
same distance as the target rather than staying put: it means "start easing off *before* the
target", and easing off two kilowatts below a ceiling we have deliberately decided not to
defend is not caution — it is discharging the home battery for a saving that cannot happen,
because the charge is already booked.

Escalation to hard has no confirmation and no dwell — by the time 120 s had confirmed, a
third of the quarter-hour it was protecting would be gone. Every **release** is the opposite:
it must hold for 120 s *and* wait out a 60 s dwell, and it must fall a further 150 W below
the limit it is leaving. Tightening early costs a slower charge; relaxing early costs money.

The hard stop **outranks the solar ride-out** — that exists to smooth *solar* dips, not to
hold the charger on through a demand-charge breach.

### The SoC ladder

Peak protection *owns* the mapped minimum-SoC number, with two values:

```
100 % ┤
      │
 80 % ┤◄══ Keep home battery above ═══ the CAR may not drain below this (the reserve line)
      │◄══ Cheap-hour target, dark day ═══ how deep cheap grid fills it when tomorrow is poor
      │
 50 % ┤◄══ Keep in reserve for peaks ═══ where minimum-SoC RESTS
      │      ordinary house loads cannot drain the battery below this, so there is
      │      always something banked for a peak nobody saw coming
      │
 40 % ┤◄══ Cheap-hour target, bright day ═══ stop buying: leave the sun somewhere to go
      │
 35 % ┤◄══ May discharge to for peaks ═══ where minimum-SoC DROPS while shaving
      │      that drop is what actually frees the headroom, and it is the only lever
  0 % ┤      that works with no car anywhere near the house
```

Those two numbers are the whole contract *while peak protection is on* — no attempt is made
to blend your own edits into them. But the contract ends when you switch it off: the
minimum-SoC number and the grid setpoint then go back to whatever they held when peak
protection first took them over, and are left alone from there. Without that hand-back,
switching off at the hard tier would leave the house commanded to import 0 W forever. Only
entities we know we took over are ever handed back, so one you manage yourself is untouched,
and the record survives a restart — otherwise a reboot mid-shave would lose the only thing
that knows the entity is ours to give back.

`May discharge to` is clamped so it can never sit above `Keep in reserve`, and the three kW
limits are likewise raised to keep `soft ≤ target ≤ hard` whichever order you set them in.

### What it actually does, by situation

| Situation | Lever |
|---|---|
| Nearing soft, car charging | Ease the wallbox back to what the budget leaves |
| Nearing soft, **no car** | Drop minimum-SoC to the peak floor, release the hold switch, abandon cheap-hour buying |
| Hard tier | All of the above, plus setpoint → 0 W and pause the car if 6 A won't fit |
| Car running on **pure solar** | Nothing — stopping it would export the surplus, not reduce the import |
| Battery already at its peak floor | Nothing left to shave with; the status sensor says so plainly |
| Month already peaked higher | The limits float up to just under it — see below |
| Back to off (tier) | minimum-SoC → the shaving reserve, setpoint → normal, the hold returns to the car brain |
| Switched off (the switch) | minimum-SoC and setpoint go back to what they held before peak protection took them over |
| Just switched into **Manual** | The house levers still act — they are peak protection's, not the wallbox's. Only the charger is left as-is (and even that yields to a hard-tier stop) |

**What it cannot do:** on a Victron ESS the setpoint already sits at ~50 W, so the battery is
*already* covering the sauna. The peak appears only when the battery physically can't — at
its minimum SoC, or at the inverter's power limit — and lowering the setpoint further does
nothing when it is already saturated. Peak protection cannot shed a load. The
`Peak shaving active` binary sensor, with its `tier` attribute, is the hook for your own
load-shedding automations.

### Don't pay twice for a peak you've already bought

A demand charge is set by the month's **single highest** quarter-hour. Once one window has
gone to 5.2 kW, holding the next one under 3.7 kW saves nothing at all — it only costs a
slower charge for the rest of the month. So with **Allow up to this month's peak** on (the
default) the limits float up to whatever the month has already cost, and the card says so.
Turn it off for a strict ceiling regardless.

**Up to it, not onto it.** Aiming exactly at the record would ratchet: the projection is an
estimate and the house is not perfectly steerable, so a window aimed at 5.2 kW eventually
lands at 5.25 — which becomes the new record, which raises the ceiling, and the month creeps
upward one overshoot at a time. So the *target* settles **Stay under the month's peak by**
below the record (0.2 kW by default) while the *hard* limit sits on the record itself:

| With a 5.2 kW record, 3.7/3.9 kW configured | In force |
|---|---|
| Start easing off at | 4.6 kW — it keeps its 0.4 kW gap below the target |
| Peak target (what the budget aims at) | 5.0 kW — the record minus the buffer |
| Never exceed (cut now, pause the car) | 5.2 kW — the record itself |

The card's gauge draws and colours these — the effective set, never the configured one, so a
window is never painted "easing off" against a line the guard has stopped enforcing.

Set the buffer to 0 to aim straight at the record. It can never make the guard *stricter*
than your own numbers: a record barely above your target leaves your target in force.

`This month's peak` only ever records windows we could actually measure: a guessed number
must never become the number the card calls your bill. Use *Reset this month's peak* if the
operator's own meter reading disagrees. There is deliberately no way to type a peak in by
hand — the record is what was measured, so a peak that happened while Home Assistant was
down is not one the guard will spend.

### When the measurement can't be trusted

If the grid reading disappears or Home Assistant restarts mid-window, part of the
quarter-hour goes unmeasured. The last reading is held across the gap (under-counting is the
one error that would let a real peak through), the window is flagged **degraded**, and from
there peak protection may **tighten but never relax** until the next clean boundary. Nothing
is written at all until a trustworthy reading has arrived — it never shaves blind on a cold
start.

A gap of more than half an hour is a **long outage**, not a gap: the window we were in is
closed, a fresh degraded one opens, and nothing in between is guessed at. That measurement
runs from the older of the last reading and the window still standing open, which is what
makes it survive a restart — with only the reading to go by, coming back after a day down
looks like a two-second gap, and back-filling a day of quarter-hours from a single live
reading would hand the month a peak it never bought.

Quarter-hours are floored in UTC. That is exact for any whole-hour UTC offset, Austria
included; a half-hour-offset zone would be aligned to the wrong boundary. The *month* the
record is filed under is your local one, though — a demand charge is billed on the calendar
on the wall, so a peak drawn at 00:30 on the first counts for the month that just started,
not the one that just ended. Any clock time in a status line is local for the same reason.

---

## Cheap-hour grid charging

Buys energy into the home battery — and runs the house from the grid — while the price is at
or below the same **Cheap price threshold** the car uses. Off by default, and it needs a
mapped grid-setpoint entity to do anything at all.

On an ESS the grid setpoint *is* total grid import, so what is commanded here is exactly the
quantity a capacity tariff bills:

```
cheap now      → setpoint = min(house load + car − PV + cheap-hour import power, budget)
not cheap      → setpoint = your normal grid import (~50 W): the battery covers the house
SoC ≥ target   → stop
peak protection engaged → abandoned outright
```

**The two features belong together.** Importing hard in a cheap hour is precisely how a
demand charge gets bought by accident. Because the command is capped by
`min(soft limit, remaining budget)`, it imports *steadily* instead of spiking — you get the
cheap energy without the peak.

### The forecast decides how deep, not whether

| Solar forecast for tomorrow | Fill to |
|---|---|
| below `pv_forecast_low_kwh` (8 kWh) — a dark day | **Cheap-hour target, dark day** (80 %) |
| above it — a bright day | **Cheap-hour target, bright day** (40 %), leaving the sun somewhere to land |
| no forecast entity mapped | always the dark-day target (the safe assumption) |

The point is not "is it winter". It is *don't fill the battery from the grid the night before
a bright day*, where the sun would have done it for free and the paid-for charge only leaves
the PV nowhere to go.

---

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
| `PEAK_WINDOW_S` | 900 s | the **billing** quarter-hour |
| `PEAK_CONFIRM_S` | 120 s | a **soft** crossing must hold this long (hard is immediate) |
| `PEAK_RELEASE_S` | 120 s | …and so must every **release**, in the other direction |
| `PEAK_DWELL_S` | 60 s | minimum time between tier changes, releases only |
| `PEAK_HYSTERESIS_W` | 150 W | how far below a limit the projection must fall to release |
| `PEAK_MAX_GAP_S` | 120 s | a longer sample gap marks the window **degraded** (tighten-only) |
| `PEAK_MIN_REMAINING_S` | 60 s | floor on "time left" when sizing the remaining budget |
| `PEAK_HISTORY_LEN` | 96 | completed quarter-hours kept for the card (24 h) |
