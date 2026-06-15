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

    const title = this._config.title ?? this._deviceName(ent?.deviceId) ?? this._t("price.title");

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
    // Domain padded so the threshold can sit a little above/below the curve.
    const lo = Math.min(...prices, effective);
    const hi = Math.max(...prices, effective);
    const span = hi - lo || 1;
    const yMin = lo - span * 0.1;
    const yMax = hi + span * 0.1;

    const x = (t: number) => PAD.left + ((t - t0) / (t1 - t0)) * PLOT_W;
    const y = (p: number) => PAD.top + (1 - (p - yMin) / (yMax - yMin)) * PLOT_H;
    const baseline = PAD.top + PLOT_H;
    const yThresh = y(effective);

    const bars = shown.map((s) => {
      const x0 = x(s.start);
      const x1 = x(s.end);
      const top = y(s.price);
      const cheapBar = s.price <= effective;
      return svg`<rect
        class="bar ${cheapBar ? "cheap" : ""}"
        x=${x0 + 0.5}
        y=${top}
        width=${Math.max(0.5, x1 - x0 - 1)}
        height=${Math.max(0, baseline - top)}
      ></rect>`;
    });

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
        @pointerdown=${this._onPointerDown}
        @pointermove=${this._onPointerMove}
        @pointerup=${this._onPointerUp}
        @pointercancel=${this._onPointerUp}
      >
        <!-- y grid: min / threshold / max -->
        <text class="y-tick" x=${PAD.left - 4} y=${y(yMax) + 3}>${this._fmtNum(hi)}</text>
        <text class="y-tick" x=${PAD.left - 4} y=${baseline}>${this._fmtNum(lo)}</text>
        ${dividers}
        ${bars}
        ${ticks}
        ${nowX !== null
          ? svg`<line class="now-line" x1=${nowX} y1=${PAD.top} x2=${nowX} y2=${baseline}></line>
                 <text class="now-tick" x=${nowX} y=${PAD.top - 2}>${this._t("price.now")}</text>`
          : nothing}
        <!-- threshold line + draggable handle -->
        <line class="thresh" x1=${PAD.left} y1=${yThresh} x2=${W - PAD.right} y2=${yThresh}></line>
        <g class="handle" data-handle>
          <rect x=${W - PAD.right - 52} y=${yThresh - 9} width="52" height="18" rx="4"></rect>
          <text x=${W - PAD.right - 26} y=${yThresh + 4}>${this._fmtNum(effective)}</text>
        </g>
      </svg>
    </div>`;
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
    (e.target as Element).setPointerCapture?.(e.pointerId);
    e.preventDefault();
    this._updateDrag(e);
  }

  private _onPointerMove(e: PointerEvent): void {
    if (!this._dragging) return;
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

    /* Chart */
    .chart {
      padding: 0 8px;
    }
    .chart svg {
      width: 100%;
      height: 200px;
      touch-action: none; /* let us own the drag gesture on touch */
    }
    .bar {
      fill: var(--divider-color);
    }
    .bar.cheap {
      fill: var(--primary-color);
    }
    .thresh {
      stroke: var(--primary-color);
      stroke-width: 1.5;
      stroke-dasharray: 4 3;
    }
    .handle rect {
      fill: var(--primary-color);
      cursor: ns-resize;
    }
    .handle text {
      fill: var(--text-primary-color, #fff);
      font-size: 11px;
      font-weight: 600;
      text-anchor: middle;
    }
    .now-line {
      stroke: var(--error-color, #db4437);
      stroke-width: 1.5;
    }
    .now-tick {
      fill: var(--error-color, #db4437);
      font-size: 9px;
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
