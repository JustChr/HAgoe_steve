import { LitElement, html, css, svg, nothing, type TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import "./goe-steve-price-card-editor";
import { resolveEntities, findDevices, type ResolvedEntities } from "./entities";
import { localize } from "./localize";

const INTEGRATION_NAME = "go-e + SteVe Smart Charging";

/** Minimal shape of the bits of `hass` we touch. */
interface HassEntity {
  entity_id: string;
  state: string;
  attributes: Record<string, any>;
}
interface Hass {
  states: Record<string, HassEntity>;
  entities: Record<string, { entity_id: string; device_id?: string; platform?: string; translation_key?: string }>;
  devices: Record<string, { name?: string; name_by_user?: string }>;
  localize: (key: string) => string;
  language?: string;
  locale?: { language?: string };
  callService: (domain: string, service: string, data: Record<string, any>) => Promise<unknown>;
}

export interface GoeStevePriceCardConfig {
  type: string;
  device?: string;
  title?: string;
  /** How many hours of forecast to show from now (default: all available, capped 48). */
  hours?: number;
  /** Length of the "cheapest window" to highlight, in hours (default 3; 0 hides it). */
  charge_hours?: number;
}

/** One forecast slot, parsed from the sensor's `slots` attribute. */
interface Slot {
  start: number; // epoch ms
  end: number; // epoch ms (next slot's start, or +1h for the last)
  price: number;
}

/** Drawing constants for the SVG chart (viewBox units). */
const W = 480;
const H = 200;
const PAD = { left: 38, right: 10, top: 12, bottom: 24 };
const PLOT_W = W - PAD.left - PAD.right;
const PLOT_H = H - PAD.top - PAD.bottom;
const HOUR_MS = 3600_000;

@customElement("goe-steve-price-card")
export class GoeStevePriceCard extends LitElement {
  @property({ attribute: false }) public hass!: Hass;
  @state() private _config!: GoeStevePriceCardConfig;
  /** Threshold being dragged (currency/kWh); null when not dragging. */
  @state() private _dragValue: number | null = null;
  /** Index (into the shown slots) of the slot under the pointer; null when none. */
  @state() private _hoverIndex: number | null = null;

  /** Highlighted "cheapest window" length in hours (config, default 3). */
  private get _chargeHours(): number {
    const h = this._config?.charge_hours;
    return h === undefined ? 3 : h;
  }

  public static getConfigElement(): HTMLElement {
    return document.createElement("goe-steve-price-card-editor");
  }

  public static getStubConfig(hass: Hass): GoeStevePriceCardConfig {
    const devices = findDevices(hass);
    return { type: "custom:goe-steve-price-card", device: devices[0]?.id };
  }

  public setConfig(config: GoeStevePriceCardConfig): void {
    this._config = { ...config };
  }

  public getCardSize(): number {
    return 6;
  }

  private get _entities(): ResolvedEntities | null {
    if (!this.hass) return null;
    return resolveEntities(this.hass, this._config?.device);
  }

  private _t(key: string, params: Record<string, string> = {}): string {
    return localize(this.hass, key, params);
  }

  private _stateObj(id?: string): HassEntity | undefined {
    return id ? this.hass.states[id] : undefined;
  }

  private _deviceName(deviceId?: string): string | null {
    if (!deviceId) return null;
    const d = this.hass.devices[deviceId];
    return d?.name_by_user || d?.name || null;
  }

  // --- Data --------------------------------------------------------------------
  /** Parsed, time-ordered slots from the price-forecast sensor. */
  private _slots(forecast: HassEntity): Slot[] {
    const raw: Array<{ start?: string; price?: number }> =
      forecast.attributes.slots ?? [];
    const parsed = raw
      .map((s) => ({ start: Date.parse(s.start ?? ""), price: Number(s.price) }))
      .filter((s) => !Number.isNaN(s.start) && !Number.isNaN(s.price))
      .sort((a, b) => a.start - b.start);
    return parsed.map((s, i) => ({
      start: s.start,
      end: i + 1 < parsed.length ? parsed[i + 1].start : s.start + HOUR_MS,
      price: s.price,
    }));
  }

  /** The cheap-price `number` entity, with its bounds (for dragging/clamping). */
  private _cheap(ent: ResolvedEntities, forecast: HassEntity) {
    const obj = this._stateObj(ent.cheap_price);
    const fromAttr = Number(forecast.attributes.cheap_price);
    const value = obj
      ? Number(obj.state)
      : Number.isNaN(fromAttr)
        ? 0.15
        : fromAttr;
    const a = obj?.attributes ?? {};
    return {
      obj,
      value,
      min: Number(a.min ?? 0),
      max: Number(a.max ?? 1),
      step: Number(a.step ?? 0.01),
      unit: (forecast.attributes.unit as string) ?? a.unit_of_measurement ?? "",
    };
  }

  // --- Render ------------------------------------------------------------------
  protected render(): TemplateResult | typeof nothing {
    if (!this.hass || !this._config) return nothing;

    const ent = this._entities;
    const forecast = this._stateObj(ent?.price_forecast);
    const slots = forecast ? this._slots(forecast) : [];

    const deviceName = this._deviceName(ent?.deviceId);
    const title =
      this._config.title ??
      (deviceName ? `${deviceName} · ${this._t("price.title")}` : this._t("price.title"));

    if (!forecast || slots.length === 0) {
      const [before, after] = this._t("price.no_price").split("{name}");
      return html`<ha-card>
        <div class="empty">
          <ha-icon icon="mdi:cash-clock"></ha-icon>
          <p>${before}<b>${INTEGRATION_NAME}</b>${after ?? ""}</p>
        </div>
      </ha-card>`;
    }

    const cheap = this._cheap(ent!, forecast);
    const effective = this._dragValue ?? cheap.value;

    return html`<ha-card>
      <div class="header">
        <div class="title-row">
          <ha-icon icon="mdi:cash-clock"></ha-icon>
          <span class="title">${title}</span>
        </div>
        <div class="now-price">${this._fmtPrice(Number(forecast.state), cheap.unit)}</div>
      </div>
      ${this._renderStats(slots, cheap.unit)}
      ${this._renderChart(slots, effective)}
      ${this._renderPreview(slots, effective)}
      ${this._renderThresholdInput(cheap, effective)}
    </ha-card>`;
  }

  // --- The chart ---------------------------------------------------------------
  /** The slots actually drawn: future slots, optionally clipped to `hours`. */
  private _shownSlots(slots: Slot[]): Slot[] {
    const now = Date.now();
    let shown = slots.filter((s) => s.end > now);
    if (shown.length === 0) shown = slots.slice(-1);
    if (this._config.hours && this._config.hours > 0) {
      const limit = now + this._config.hours * HOUR_MS;
      shown = shown.filter((s) => s.start < limit);
    }
    return shown.slice(0, 96); // hard safety cap
  }

  private _renderChart(slots: Slot[], effective: number): TemplateResult {
    const now = Date.now();
    const shown = this._shownSlots(slots);

    const t0 = shown[0].start;
    const t1 = shown[shown.length - 1].end;
    const prices = shown.map((s) => s.price);
    const loPrice = Math.min(...prices);
    const hiPrice = Math.max(...prices);
    // Domain padded so the threshold can sit a little above/below the curve.
    const lo = Math.min(loPrice, effective);
    const hi = Math.max(hiPrice, effective);
    const span = hi - lo || 1;
    const yMin = lo - span * 0.1;
    const yMax = hi + span * 0.1;

    const x = (t: number) => PAD.left + ((t - t0) / (t1 - t0)) * PLOT_W;
    const y = (p: number) => PAD.top + (1 - (p - yMin) / (yMax - yMin)) * PLOT_H;
    const baseline = PAD.top + PLOT_H;
    const yThresh = y(effective);
    const avg = this._weightedMean(shown);
    const yAvg = y(avg);

    const bars = shown.map((s, i) => {
      const x0 = x(s.start);
      const x1 = x(s.end);
      const top = y(s.price);
      const isCheap = s.price <= effective;
      const isNow = now >= s.start && now < s.end;
      const isHover = i === this._hoverIndex;
      return svg`<rect
        class="bar ${isNow ? "now-bar" : ""} ${isHover ? "hover-bar" : ""}"
        fill=${this._barFill(s.price, isCheap, effective, hiPrice)}
        x=${x0 + 0.5}
        y=${top}
        width=${Math.max(0.5, x1 - x0 - 1)}
        height=${Math.max(0, baseline - top)}
      ></rect>`;
    });

    // Cheapest contiguous charging window (Tier 1 — the "charge here" cue).
    const best = this._chargeHours > 0 ? this._bestWindow(shown, this._chargeHours) : null;
    const window =
      best && best.endIdx > best.startIdx - 1
        ? (() => {
            const wx0 = x(best.start);
            const wx1 = x(best.end);
            return svg`<g class="best-window">
              <rect x=${wx0} y=${PAD.top} width=${Math.max(0, wx1 - wx0)} height=${PLOT_H}></rect>
              <line x1=${wx0} y1=${PAD.top} x2=${wx0} y2=${baseline}></line>
              <line x1=${wx1} y1=${PAD.top} x2=${wx1} y2=${baseline}></line>
              <text x=${(wx0 + wx1) / 2} y=${PAD.top + 21}>${this._t("price.cheapest_window", {
                hours: this._fmtHours(this._chargeHours),
              })}</text>
            </g>`;
          })()
        : nothing;

    // Vertical day-boundary dividers + "Tomorrow" label at each local midnight.
    const dividers: TemplateResult[] = [];
    for (const s of shown) {
      const d = new Date(s.start);
      if (d.getHours() === 0 && d.getMinutes() === 0 && s.start > t0) {
        const dx = x(s.start);
        dividers.push(svg`<line class="day-div" x1=${dx} y1=${PAD.top} x2=${dx} y2=${baseline}></line>`);
        dividers.push(svg`<text class="day-lbl" x=${dx + 3} y=${PAD.top + 9}>${this._t("price.tomorrow")}</text>`);
      }
    }

    // Sparse hour ticks (every 6h on the clock).
    const ticks: TemplateResult[] = [];
    for (const s of shown) {
      const d = new Date(s.start);
      if (d.getHours() % 6 === 0 && d.getMinutes() === 0) {
        const tx = x(s.start);
        ticks.push(svg`<text class="x-tick" x=${tx} y=${H - 8}>${String(d.getHours()).padStart(2, "0")}</text>`);
      }
    }

    const nowX = now >= t0 && now <= t1 ? x(now) : null;

    return html`<div class="chart">
      <svg
        viewBox="0 0 ${W} ${H}"
        preserveAspectRatio="none"
        @pointermove=${this._onPointerMove}
        @pointerdown=${this._onChartPointerDown}
        @pointerup=${this._onPointerUp}
        @pointercancel=${this._onPointerUp}
        @pointerleave=${this._onPointerLeave}
      >
        <!-- y grid: min / avg / threshold / max -->
        <text class="y-tick" x=${PAD.left - 4} y=${y(yMax) + 3}>${this._fmtNum(hi)}</text>
        <text class="y-tick" x=${PAD.left - 4} y=${baseline}>${this._fmtNum(lo)}</text>
        <text class="y-tick thresh-tick" x=${PAD.left - 4} y=${yThresh + 3}>${this._fmtNum(effective)}</text>
        ${window}
        ${dividers}
        ${bars}
        ${ticks}
        <!-- average reference line -->
        <line class="avg-line" x1=${PAD.left} y1=${yAvg} x2=${W - PAD.right} y2=${yAvg}></line>
        <text class="avg-lbl" x=${PAD.left + 2} y=${yAvg - 2}>Ø</text>
        ${nowX !== null
          ? svg`<line class="now-line" x1=${nowX} y1=${PAD.top} x2=${nowX} y2=${baseline}></line>
                 <text class="now-tick" x=${nowX} y=${PAD.top - 2}>${this._t("price.now")}</text>`
          : nothing}
        <!-- threshold line + draggable handle -->
        <line class="thresh" x1=${PAD.left} y1=${yThresh} x2=${W - PAD.right} y2=${yThresh}></line>
        <g class="handle" data-handle @pointerdown=${this._onPointerDown}>
          <!-- generous, invisible touch target so fingers can grab the handle -->
          <rect class="handle-hit" x=${W - PAD.right - 68} y=${yThresh - 20} width="72" height="40"></rect>
          <rect class="handle-chip" x=${W - PAD.right - 52} y=${yThresh - 9} width="52" height="18" rx="4"></rect>
          <text x=${W - PAD.right - 26} y=${yThresh + 4}>${this._fmtNum(effective)}</text>
        </g>
      </svg>
      ${this._renderTooltip(shown, x, y)}
    </div>`;
  }

  /** Fill color for a price bar: cheap → accent, negative → green, else amber→red heat. */
  private _barFill(price: number, isCheap: boolean, effective: number, hiPrice: number): string {
    if (price < 0) return "var(--success-color, #2e7d32)";
    if (isCheap) return "var(--success-color, #2e7d32)";
    // Warm gradient scaled from just-above-threshold (amber) to the peak (red).
    const range = hiPrice - effective || 1;
    const t = Math.max(0, Math.min(1, (price - effective) / range));
    const hue = 45 - t * 37; // 45° amber → 8° red-orange
    const light = 55 - t * 8;
    return `hsl(${hue.toFixed(0)}, 85%, ${light.toFixed(0)}%)`;
  }

  /** Duration-weighted mean price across the given slots. */
  private _weightedMean(slots: Slot[]): number {
    let dur = 0;
    let cost = 0;
    for (const s of slots) {
      const d = (s.end - s.start) / HOUR_MS;
      dur += d;
      cost += s.price * d;
    }
    return dur > 0 ? cost / dur : 0;
  }

  /** Cheapest contiguous block covering at least `hours`, by duration-weighted mean. */
  private _bestWindow(
    slots: Slot[],
    hours: number,
  ): { start: number; end: number; mean: number; startIdx: number; endIdx: number } | null {
    let best: { start: number; end: number; mean: number; startIdx: number; endIdx: number } | null =
      null;
    for (let i = 0; i < slots.length; i++) {
      let dur = 0;
      let cost = 0;
      let j = i;
      while (j < slots.length && dur < hours - 1e-9) {
        const d = (slots[j].end - slots[j].start) / HOUR_MS;
        dur += d;
        cost += slots[j].price * d;
        j++;
      }
      if (dur < hours - 1e-9) break; // can't fill the window from here on → nor from any later i
      const mean = cost / dur;
      if (!best || mean < best.mean) {
        best = { start: slots[i].start, end: slots[j - 1].end, mean, startIdx: i, endIdx: j - 1 };
      }
    }
    return best;
  }

  // --- Hover tooltip -----------------------------------------------------------
  private _renderTooltip(
    shown: Slot[],
    x: (t: number) => number,
    y: (p: number) => number,
  ): TemplateResult | typeof nothing {
    const i = this._hoverIndex;
    if (i === null || i < 0 || i >= shown.length) return nothing;
    const s = shown[i];
    const cx = (x(s.start) + x(s.end)) / 2;
    // Horizontal: map viewBox x back to the padded content width (svg has 8px side padding).
    const leftPct = (cx / W) * 100;
    const topPx = Math.max(2, y(s.price) - 4); // svg is 1:1 vertically (H === px height)
    const unit = this._entities && this._stateObj(this._entities.price_forecast)?.attributes.unit;
    return html`<div
      class="tip"
      style="left: calc(8px + ${leftPct.toFixed(2)}% - ${(leftPct / 100 * 16).toFixed(2)}px); top: ${topPx}px;"
    >
      <span class="tip-time">${this._fmtTime(s.start)}–${this._fmtTime(s.end)}</span>
      <span class="tip-price">${this._fmtNum(s.price)}${unit ? ` ${unit}` : ""}</span>
    </div>`;
  }

  /** Hit-test the pointer's X against the shown slots; returns the index or null. */
  private _slotAtClientX(clientX: number): number | null {
    const ent = this._entities;
    const forecast = this._stateObj(ent?.price_forecast);
    const slots = forecast ? this._slots(forecast) : [];
    const shown = this._shownSlots(slots);
    if (shown.length === 0) return null;
    const svgEl = this.renderRoot.querySelector("svg");
    if (!svgEl) return null;
    const rect = svgEl.getBoundingClientRect();
    const t0 = shown[0].start;
    const t1 = shown[shown.length - 1].end;
    const frac = (clientX - rect.left) / rect.width;
    const vx = frac * W; // viewBox x
    if (vx < PAD.left || vx > W - PAD.right) return null;
    const t = t0 + ((vx - PAD.left) / PLOT_W) * (t1 - t0);
    const idx = shown.findIndex((s) => t >= s.start && t < s.end);
    return idx >= 0 ? idx : null;
  }

  private _onChartPointerDown(e: PointerEvent): void {
    // A tap on a bar (e.g. touch) reveals its tooltip; the handle stops propagation.
    if (this._dragging) return;
    this._hoverIndex = this._slotAtClientX(e.clientX);
  }

  private _onPointerLeave(): void {
    if (this._hoverIndex !== null) this._hoverIndex = null;
  }

  // --- Drag handling (pointer = mouse + touch) ---------------------------------
  private _dragging = false;
  private _cheapCache: ReturnType<typeof this._cheap> | null = null;

  private _onPointerDown(e: PointerEvent): void {
    const ent = this._entities;
    const forecast = this._stateObj(ent?.price_forecast);
    if (!ent || !forecast || !ent.cheap_price) return;
    this._cheapCache = this._cheap(ent, forecast);
    this._dragging = true;
    this._hoverIndex = null;
    (e.target as Element).setPointerCapture?.(e.pointerId);
    e.preventDefault();
    this._updateDrag(e);
  }

  private _onPointerMove(e: PointerEvent): void {
    if (!this._dragging) {
      // Not dragging → track the slot under the pointer for the tooltip.
      const idx = this._slotAtClientX(e.clientX);
      if (idx !== this._hoverIndex) this._hoverIndex = idx;
      return;
    }
    this._hoverIndex = null;
    e.preventDefault();
    this._updateDrag(e);
  }

  private _onPointerUp(): void {
    if (!this._dragging) return;
    this._dragging = false;
    const cheap = this._cheapCache;
    const value = this._dragValue;
    this._dragValue = null;
    this._cheapCache = null;
    if (cheap?.obj && value !== null && value !== cheap.value) {
      this.hass.callService("number", "set_value", {
        entity_id: cheap.obj.entity_id,
        value,
      });
    }
  }

  /** Map the pointer's Y to a price, clamped to the entity bounds and snapped. */
  private _updateDrag(e: PointerEvent): void {
    const cheap = this._cheapCache;
    if (!cheap) return;
    const svgEl = this.renderRoot.querySelector("svg");
    if (!svgEl) return;
    const rect = svgEl.getBoundingClientRect();
    const relY = ((e.clientY - rect.top) / rect.height) * H;
    // Invert the y scale using the *current* domain (recomputed from shown slots).
    const { yMin, yMax } = this._yDomain(cheap);
    const frac = 1 - (relY - PAD.top) / PLOT_H;
    let price = yMin + frac * (yMax - yMin);
    price = Math.min(cheap.max, Math.max(cheap.min, price));
    if (cheap.step > 0) price = Math.round(price / cheap.step) * cheap.step;
    // Avoid float dust from the snap (e.g. 0.150000002).
    const decimals = (String(cheap.step).split(".")[1] ?? "").length || 2;
    this._dragValue = Number(price.toFixed(decimals));
  }

  /** Recompute the y-domain the chart is currently using (mirrors _renderChart). */
  private _yDomain(cheap: ReturnType<typeof this._cheap>): { yMin: number; yMax: number } {
    const ent = this._entities;
    const forecast = this._stateObj(ent?.price_forecast);
    const slots = forecast ? this._slots(forecast) : [];
    const shown = this._shownSlots(slots);
    const effective = this._dragValue ?? cheap.value;
    const prices = shown.map((s) => s.price);
    const lo = Math.min(...prices, effective);
    const hi = Math.max(...prices, effective);
    const span = hi - lo || 1;
    return { yMin: lo - span * 0.1, yMax: hi + span * 0.1 };
  }

  // --- Preview line ------------------------------------------------------------
  private _renderPreview(slots: Slot[], effective: number): TemplateResult {
    const now = Date.now();
    const upcoming = slots.filter((s) => s.end > now);
    const cheapSlots = upcoming.filter((s) => s.price <= effective);

    if (cheapSlots.length === 0) {
      return html`<div class="preview muted">
        <ha-icon icon="mdi:flash-off"></ha-icon><span>${this._t("price.no_cheap")}</span>
      </div>`;
    }

    const hours = cheapSlots.reduce(
      (acc, s) => acc + (Math.min(s.end, now + 48 * HOUR_MS) - Math.max(s.start, now)) / HOUR_MS,
      0,
    );
    // First contiguous cheap window from now.
    const first = cheapSlots[0];
    let windowEnd = first.end;
    for (let i = 1; i < cheapSlots.length; i++) {
      if (cheapSlots[i].start === windowEnd) windowEnd = cheapSlots[i].end;
      else break;
    }
    const hoursLabel = `${hours.toFixed(hours < 10 ? 1 : 0)} h`;

    return html`<div class="preview">
      <ha-icon icon="mdi:flash"></ha-icon>
      <span>${this._t("price.cheap_hours", { hours: hoursLabel })}</span>
      <span class="sep">·</span>
      <span class="muted"
        >${this._t("price.next_window", {
          start: this._fmtTime(Math.max(first.start, now)),
          end: this._fmtTime(windowEnd),
        })}</span
      >
    </div>`;
  }

  // --- Stat row (min · avg · max) ----------------------------------------------
  private _renderStats(slots: Slot[], unit: string): TemplateResult | typeof nothing {
    const shown = this._shownSlots(slots);
    if (shown.length === 0) return nothing;
    const prices = shown.map((s) => s.price);
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const avg = this._weightedMean(shown);
    const u = unit ? ` ${unit}` : "";
    return html`<div class="stats">
      <span class="stat"><span class="stat-k stat-min">▼</span>${this._fmtNum(min)}${u}</span>
      <span class="stat"><span class="stat-k">${this._t("price.avg")}</span>${this._fmtNum(avg)}${u}</span>
      <span class="stat"><span class="stat-k stat-max">▲</span>${this._fmtNum(max)}${u}</span>
    </div>`;
  }

  // --- Numeric threshold input (precise entry / mobile fallback) ---------------
  private _renderThresholdInput(
    cheap: ReturnType<typeof this._cheap>,
    effective: number,
  ): TemplateResult | typeof nothing {
    if (!cheap.obj) return nothing;
    return html`<div class="threshold-row">
      <span class="thr-label">${this._t("price.cheap_threshold")}</span>
      <span class="thr-input">
        <input
          type="number"
          .value=${String(effective)}
          min=${cheap.min}
          max=${cheap.max}
          step=${cheap.step}
          @change=${(e: Event) => this._setThreshold(cheap, (e.target as HTMLInputElement).value)}
        />
        ${cheap.unit ? html`<span class="thr-unit">${cheap.unit}</span>` : nothing}
      </span>
    </div>`;
  }

  private _setThreshold(cheap: ReturnType<typeof this._cheap>, raw: string): void {
    const num = Number(raw);
    if (!cheap.obj || Number.isNaN(num) || num === cheap.value) return;
    this.hass.callService("number", "set_value", {
      entity_id: cheap.obj.entity_id,
      value: num,
    });
  }

  // --- Formatting --------------------------------------------------------------
  private _fmtNum(v: number): string {
    return v.toFixed(Math.abs(v) < 1 ? 2 : 1);
  }
  private _fmtPrice(v: number, unit: string): string {
    if (Number.isNaN(v)) return "—";
    return `${this._fmtNum(v)}${unit ? ` ${unit}` : ""}`;
  }
  private _fmtHours(h: number): string {
    return Number.isInteger(h) ? String(h) : h.toFixed(1);
  }
  private _fmtTime(ms: number): string {
    return new Date(ms).toLocaleTimeString(this.hass?.locale?.language ?? [], {
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  static styles = css`
    ha-card {
      overflow: hidden;
      padding-bottom: 8px;
    }
    .empty {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      padding: 24px;
      color: var(--secondary-text-color);
      text-align: center;
    }
    .empty ha-icon {
      --mdc-icon-size: 40px;
      color: var(--disabled-text-color);
    }
    .header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 16px 16px 8px;
    }
    .title-row {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .title-row ha-icon {
      color: var(--primary-color);
    }
    .title {
      font-size: 1.25rem;
      font-weight: 500;
    }
    .now-price {
      font-size: 1.1rem;
      font-weight: 600;
      color: var(--primary-text-color);
    }

    /* Stat row */
    .stats {
      display: flex;
      gap: 16px;
      padding: 0 16px 4px;
      font-size: 0.85rem;
      color: var(--secondary-text-color);
    }
    .stat {
      display: inline-flex;
      align-items: baseline;
      gap: 4px;
    }
    .stat-k {
      font-size: 0.75rem;
      opacity: 0.9;
    }
    .stat-min {
      color: var(--success-color, #2e7d32);
    }
    .stat-max {
      color: hsl(8, 85%, 47%);
    }

    /* Chart */
    .chart {
      padding: 0 8px;
      position: relative;
    }
    .chart svg {
      width: 100%;
      height: 200px;
      /* default touch-action: vertical swipes scroll the page normally;
         only the handle (below) owns the drag gesture. */
    }
    /* Bar fill is set inline per-bar (heat gradient / accent / negative),
       so no base fill here — a CSS fill would override the attribute. */
    .now-bar {
      stroke: var(--primary-text-color);
      stroke-width: 1;
    }
    .hover-bar {
      filter: brightness(1.12);
    }

    /* Cheapest-window highlight — green, matching the "cheap" bars */
    .best-window rect {
      fill: var(--success-color, #2e7d32);
      opacity: 0.12;
      pointer-events: none;
    }
    .best-window line {
      stroke: var(--success-color, #2e7d32);
      stroke-width: 1;
      stroke-dasharray: 3 2;
      opacity: 0.7;
      pointer-events: none;
    }
    .best-window text {
      fill: var(--success-color, #2e7d32);
      font-size: 9px;
      font-weight: 600;
      text-anchor: middle;
      pointer-events: none;
    }

    /* Average reference line */
    .avg-line {
      stroke: var(--secondary-text-color);
      stroke-width: 1;
      stroke-dasharray: 1 3;
      opacity: 0.6;
    }
    .avg-lbl {
      fill: var(--secondary-text-color);
      font-size: 9px;
    }

    /* Hover tooltip */
    .tip {
      position: absolute;
      transform: translate(-50%, -100%);
      pointer-events: none;
      background: var(--primary-text-color);
      color: var(--card-background-color, var(--ha-card-background, #fff));
      border-radius: 6px;
      padding: 3px 7px;
      font-size: 0.72rem;
      line-height: 1.35;
      white-space: nowrap;
      display: flex;
      flex-direction: column;
      align-items: center;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
      z-index: 2;
    }
    .tip-price {
      font-weight: 600;
    }
    .thresh {
      stroke: var(--primary-color);
      stroke-width: 1.5;
      stroke-dasharray: 4 3;
    }
    .handle {
      /* the handle is the only element that owns the touch gesture, so a
         scroll swipe elsewhere on the chart pans the page as usual. */
      touch-action: none;
    }
    .handle rect {
      cursor: ns-resize;
      touch-action: none;
    }
    .handle-chip {
      fill: var(--primary-color);
    }
    .handle-hit {
      fill: transparent;
    }
    .handle text {
      fill: var(--text-primary-color, #fff);
      font-size: 11px;
      font-weight: 600;
      text-anchor: middle;
    }
    .now-line {
      stroke: var(--primary-text-color);
      stroke-width: 1.5;
    }
    .now-tick {
      fill: var(--primary-text-color);
      font-size: 9px;
      font-weight: 600;
      text-anchor: middle;
    }
    .day-div {
      stroke: var(--divider-color);
      stroke-width: 1;
      stroke-dasharray: 2 3;
    }
    .day-lbl {
      fill: var(--secondary-text-color);
      font-size: 9px;
    }
    .x-tick {
      fill: var(--secondary-text-color);
      font-size: 9px;
      text-anchor: middle;
    }
    .y-tick {
      fill: var(--secondary-text-color);
      font-size: 9px;
      text-anchor: end;
    }
    .thresh-tick {
      fill: var(--primary-color);
      font-weight: 600;
    }

    /* Preview */
    .preview {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 6px 16px 2px;
      font-size: 0.9rem;
      color: var(--primary-text-color);
    }
    .preview ha-icon {
      --mdc-icon-size: 18px;
      color: var(--primary-color);
    }
    .preview.muted,
    .preview .muted {
      color: var(--secondary-text-color);
    }
    .preview.muted ha-icon {
      color: var(--secondary-text-color);
    }
    .preview .sep {
      color: var(--secondary-text-color);
    }

    /* Threshold numeric input */
    .threshold-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 8px 16px 4px;
    }
    .thr-label {
      color: var(--secondary-text-color);
      font-size: 0.9rem;
    }
    .thr-input {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .thr-input input {
      width: 90px;
      padding: 8px 10px;
      border-radius: 8px;
      border: 1px solid var(--divider-color);
      background: var(--card-background-color, var(--ha-card-background));
      color: var(--primary-text-color);
      font-family: inherit;
      font-size: 0.95rem;
      text-align: right;
    }
    .thr-input input:focus {
      outline: none;
      border-color: var(--primary-color);
    }
    .thr-unit {
      color: var(--secondary-text-color);
      font-size: 0.85rem;
    }
  `;
}

// Register in the card picker.
(window as any).customCards = (window as any).customCards || [];
(window as any).customCards.push({
  type: "goe-steve-price-card",
  name: "go-e + SteVe Price",
  description:
    "Electricity-price forecast with a draggable 'cheap' threshold — see the curve and set what counts as cheap.",
  preview: true,
  documentationURL: "https://github.com/JustChr/HAgoe_steve",
});
