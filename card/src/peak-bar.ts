/**
 * The quarter-hour gauge, shared by both cards.
 *
 * The capacity tariff bills the highest average grid import over a *fixed clock
 * quarter-hour*, so the one thing this has to communicate is: where is the current
 * quarter-hour heading, and how does that compare with the limits? Hence a solid
 * fill for what the window has already drawn, a lighter ghost extending to the
 * projection, and tick marks the eye can read against without a legend.
 *
 * Lives in its own module so the strip on the main card and the gauge on the peak
 * card are literally the same widget rather than two that drift apart.
 */

import { css, html, nothing, TemplateResult } from "lit";

export interface PeakBarData {
  /** Average grid import so far this quarter-hour (W). */
  averageW: number;
  /** Where that average lands if the present draw holds (W). */
  projectedW: number;
  /**
   * The three limits as *configured*. Kept so the card can spot that the month
   * allowance is doing something (see `effectiveTargetW` below) — never for
   * drawing or colouring, which always go by the effective set: painting a window
   * "easing off" at a line the engine has stopped enforcing is alarming about
   * nothing.
   */
  softW: number;
  targetW: number;
  hardW: number;
  /** The soft line actually in force — it travels with the target below. */
  effectiveSoftW: number;
  /** The target actually in force — differs when the month allowance applies. */
  effectiveTargetW: number;
  /** Likewise the hard limit: with the allowance on it sits on the month's record. */
  effectiveHardW: number;
  /** Part of the window went unmeasured, so the numbers are a floor, not a fact. */
  degraded: boolean;
  tier: string;
}

/** Read the bar's data off the `peak_window_power` sensor, or null if unusable. */
export function readPeakBar(state: {
  state: string;
  attributes: Record<string, unknown>;
} | undefined): PeakBarData | null {
  if (!state || ["unknown", "unavailable", ""].includes(state.state)) return null;
  const average = Number(state.state);
  if (Number.isNaN(average)) return null;
  const num = (key: string, fallback: number): number => {
    const value = Number(state.attributes[key]);
    return Number.isNaN(value) ? fallback : value;
  };
  const soft = num("soft_w", 3300);
  const target = num("target_w", 3700);
  const hard = num("hard_w", 3900);
  return {
    averageW: average,
    projectedW: num("projected_w", average),
    softW: soft,
    targetW: target,
    hardW: hard,
    effectiveSoftW: num("effective_soft_w", soft),
    effectiveTargetW: num("effective_target_w", target),
    effectiveHardW: num("effective_hard_w", hard),
    degraded: state.attributes.degraded === true,
    tier: String(state.attributes.tier ?? "off"),
  };
}

/** Which colour band a power sits in — the same thresholds the engine uses.
 *
 * Against the limits *in force*: while the month allowance is lifting the ceiling,
 * painting 4 kW red because it beats a 3.9 kW setting the engine is not enforcing
 * would be alarming about nothing.
 */
function band(watts: number, data: PeakBarData): string {
  if (watts >= data.effectiveHardW) return "hard";
  if (watts >= data.effectiveSoftW) return "soft";
  return "ok";
}

/**
 * Render the gauge.
 *
 * The scale runs to a quarter past the hard limit so the bar never pins to the
 * end: a projection *over* the limit is exactly the case worth seeing, and a full
 * bar would hide how far over it is.
 */
export function renderPeakBar(
  data: PeakBarData,
  labels: { left: string; right: string },
): TemplateResult {
  const scale = Math.max(data.effectiveHardW * 1.25, data.projectedW * 1.05, 1);
  const pct = (watts: number) => Math.max(0, Math.min(100, (watts / scale) * 100));
  const fill = pct(data.averageW);
  // Only the part of the projection that lies *beyond* what has been drawn — the
  // ghost is "where this is going", not a second reading of where it is.
  const ghost = Math.max(0, pct(data.projectedW) - fill);
  const tone = band(data.projectedW, data);

  const tick = (watts: number, cls: string, label: string) =>
    watts <= 0 || watts >= scale
      ? nothing
      : html`<span class="pb-tick ${cls}" style="left:${pct(watts)}%" title="${label}"></span>`;

  return html`<div class="pb">
    <div class="pb-track ${data.degraded ? "degraded" : ""}">
      <span class="pb-fill ${tone}" style="width:${fill}%"></span>
      <span class="pb-ghost ${tone}" style="left:${fill}%;width:${ghost}%"></span>
      ${tick(data.effectiveSoftW, "soft", labels.left)}
      ${tick(data.effectiveTargetW, "target", "")}
      ${tick(data.effectiveHardW, "hard", "")}
    </div>
    <div class="pb-labels">
      <span>${labels.left}</span>
      <span class="pb-right">${labels.right}</span>
    </div>
  </div>`;
}

/** Styles for the gauge, spread into each card's own `static styles`. */
export const peakBarStyles = css`
  .pb {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .pb-track {
    position: relative;
    height: 10px;
    border-radius: 999px;
    background: var(--divider-color);
    overflow: hidden;
  }
  .pb-track.degraded {
    /* Hatched: the number is a floor we can stand behind, not a measurement. */
    background-image: repeating-linear-gradient(
      45deg,
      transparent 0 4px,
      var(--card-background-color) 4px 8px
    );
  }
  .pb-fill,
  .pb-ghost {
    position: absolute;
    top: 0;
    bottom: 0;
  }
  .pb-fill {
    left: 0;
    border-radius: 999px 0 0 999px;
  }
  .pb-fill.ok {
    background: var(--goe-battery);
  }
  .pb-fill.soft {
    background: var(--warning-color, #c05252);
  }
  .pb-fill.hard {
    background: var(--error-color, #db4437);
  }
  .pb-ghost {
    opacity: 0.35;
  }
  .pb-ghost.ok {
    background: var(--goe-battery);
  }
  .pb-ghost.soft {
    background: var(--warning-color, #c05252);
  }
  .pb-ghost.hard {
    background: var(--error-color, #db4437);
  }
  .pb-tick {
    position: absolute;
    top: -2px;
    bottom: -2px;
    width: 2px;
    background: var(--primary-text-color);
    opacity: 0.45;
  }
  .pb-tick.hard {
    opacity: 0.75;
  }
  .pb-labels {
    display: flex;
    justify-content: space-between;
    gap: 8px;
    font-size: 0.72rem;
    color: var(--secondary-text-color);
    font-variant-numeric: tabular-nums;
  }
  .pb-right {
    text-align: right;
  }
`;
