import { LitElement, html, css, nothing, type TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import "./goe-steve-peak-card-editor";
import { resolveEntities, findDevices, type ResolvedEntities } from "./entities";
import { localize } from "./localize";
import { peakBarStyles, readPeakBar, renderPeakBar } from "./peak-bar";

const INTEGRATION_NAME = "go-e + SteVe Smart Charging";

/** Minimal shape of the bits of `hass` we touch (avoids pulling HA's types). */
interface HassEntity {
  entity_id: string;
  state: string;
  attributes: Record<string, any>;
}
interface Hass {
  states: Record<string, HassEntity>;
  entities: Record<
    string,
    { entity_id: string; device_id?: string; platform?: string; translation_key?: string }
  >;
  devices: Record<string, { name?: string; name_by_user?: string }>;
  localize: (key: string) => string;
  language?: string;
  locale?: { language?: string };
  callService: (domain: string, service: string, data: Record<string, any>) => Promise<unknown>;
}

export interface GoeStevePeakCardConfig {
  type: string;
  device?: string;
  title?: string;
  /**
   * What the grid operator charges per kW of monthly peak. Purely a display
   * multiplier for the "this is costing you X" line — a tariff constant, not
   * something the integration could know, so it lives in the card config.
   */
  demand_rate?: number;
  /** Currency symbol shown beside it. */
  currency?: string;
  /** Show the editable settings block (default true). */
  show_settings?: boolean;
}

const HOUR_MS = 3600_000;

const num = (v: unknown): number => {
  const n = Number(v);
  return Number.isNaN(n) ? NaN : n;
};

/** `min`/`max` only mean something if the entity actually reports them. */
const bound = (v: unknown): string | undefined => {
  const n = num(v);
  return Number.isNaN(n) ? undefined : String(n);
};

/** Seconds → "3:07", for the countdown to the end of the quarter-hour. */
const fmtClock = (secs: number): string => {
  const s = Math.max(0, Math.round(secs));
  const m = Math.floor(s / 60);
  return `${m}:${String(s % 60).padStart(2, "0")}`;
};

/**
 * The peak card: what the capacity tariff is going to bill, and why.
 *
 * The main card answers "what is the car doing?". This one answers a different
 * question — "is this month going to cost me a demand charge, and what is the
 * brain doing about it?" — which is why it is a separate card rather than another
 * section grafted onto an already-dense one.
 */
@customElement("goe-steve-peak-card")
export class GoeStevePeakCard extends LitElement {
  @property({ attribute: false }) public hass!: Hass;
  @state() private _config!: GoeStevePeakCardConfig;
  /** Wall clock, ticked once a second so the countdown runs without an entity update. */
  @state() private _now = Date.now();
  private _timer?: number;

  public static getConfigElement(): HTMLElement {
    return document.createElement("goe-steve-peak-card-editor");
  }

  public static getStubConfig(hass: Hass): GoeStevePeakCardConfig {
    const devices = findDevices(hass as any);
    return { type: "custom:goe-steve-peak-card", device: devices[0]?.id };
  }

  public setConfig(config: GoeStevePeakCardConfig): void {
    this._config = { show_settings: true, ...config };
  }

  public getCardSize(): number {
    return 6;
  }

  public connectedCallback(): void {
    super.connectedCallback();
    this._timer = window.setInterval(() => {
      this._now = Date.now();
    }, 1000);
  }

  public disconnectedCallback(): void {
    super.disconnectedCallback();
    if (this._timer) window.clearInterval(this._timer);
  }

  private get _entities(): ResolvedEntities | undefined {
    if (!this.hass) return undefined;
    return resolveEntities(this.hass as any, this._config?.device);
  }

  private _t(key: string, params: Record<string, string> = {}): string {
    return localize(this.hass, key, params);
  }

  private _stateObj(id: string | undefined): HassEntity | undefined {
    return id ? this.hass.states[id] : undefined;
  }

  private _deviceName(id: string): string | undefined {
    const device = this.hass.devices?.[id];
    return device?.name_by_user || device?.name;
  }

  protected render(): TemplateResult | typeof nothing {
    if (!this.hass || !this._config) return nothing;
    const ent = this._entities;
    if (!ent || !ent.deviceId || !ent.peak_window_power) {
      return html`<ha-card>
        <div class="empty">
          <ha-icon icon="mdi:transmission-tower-off"></ha-icon>
          <p>${this._renderNoDevice()}</p>
        </div>
      </ha-card>`;
    }

    const title =
      this._config.title ?? this._deviceName(ent.deviceId) ?? this._t("peak.title");

    return html`<ha-card>
      <div class="hacard">
        ${this._renderHead(title)} ${this._renderMonth(ent)} ${this._renderWindow(ent)}
        ${this._renderWhy(ent)} ${this._renderRecent(ent)} ${this._renderBuying(ent)}
        ${this._config.show_settings ? this._renderSettings(ent) : nothing}
      </div>
    </ha-card>`;
  }

  private _renderNoDevice(): TemplateResult {
    const [before, after] = this._t("card.no_device").split("{name}");
    return html`${before}<b>${INTEGRATION_NAME}</b>${after ?? ""}`;
  }

  private _renderHead(title: string): TemplateResult {
    return html`<div class="c-head">
      <ha-icon icon="mdi:transmission-tower-off"></ha-icon>
      <span class="title">${title}</span>
    </div>`;
  }

  // --- The month hero: the number that actually gets billed --------------------
  private _renderMonth(ent: ResolvedEntities): TemplateResult {
    const monthly = this._stateObj(ent.monthly_peak);
    const peakW = num(monthly?.state);
    const atRisk = monthly?.attributes?.record_at_risk === true;
    const at = monthly?.attributes?.peak_at as string | undefined;

    const value =
      Number.isNaN(peakW) || peakW <= 0
        ? this._t("peak.month_none")
        : `${(peakW / 1000).toFixed(2)} kW`;

    const rate = this._config.demand_rate;
    const cost =
      rate && !Number.isNaN(peakW) && peakW > 0
        ? this._t("peak.month_cost", {
            cost: `${((peakW / 1000) * rate).toFixed(2)} ${this._config.currency ?? ""}`.trim(),
            rate: `${rate} ${this._config.currency ?? ""}`.trim(),
          })
        : "";

    return html`<div class="month">
      <div class="month-label">${this._t("peak.month_label")}</div>
      <div class="month-value ${atRisk ? "risk" : ""}">${value}</div>
      <div class="month-sub">
        ${at ? this._t("peak.month_at", { when: this._fmtDate(at) }) : ""}
        ${cost ? html`<span class="cost">${cost}</span>` : nothing}
      </div>
      ${atRisk
        ? html`<div class="risk-note">
            <ha-icon icon="mdi:alert"></ha-icon>${this._t("peak.record_risk")}
          </div>`
        : nothing}
    </div>`;
  }

  // --- The live quarter-hour ----------------------------------------------------
  private _renderWindow(ent: ResolvedEntities): TemplateResult | typeof nothing {
    const stateObj = this._stateObj(ent.peak_window_power);
    const data = readPeakBar(stateObj);
    if (!data) return nothing;

    const ends = this._countdown(stateObj?.attributes?.window_ends);
    const right =
      ends === null ? "" : this._t("peak.time_left", { time: fmtClock(ends) });
    const left = this._t("peak.heading_for", {
      projected: (data.projectedW / 1000).toFixed(2),
    });

    // The gap between the configured target and the one in force is the month
    // allowance doing its job; unexplained it would just look like a bug. Both
    // numbers are shown, so the small step down from the record — the buffer that
    // keeps the allowance from ratcheting the peak upward — explains itself.
    const monthPeakW = num(stateObj?.attributes?.month_peak_w);
    const allowance =
      data.effectiveTargetW > data.targetW + 1
        ? html`<div class="note">
            ${this._t("peak.allowance", {
              value: (data.effectiveTargetW / 1000).toFixed(2),
              month: (
                (Number.isNaN(monthPeakW) ? data.effectiveHardW : monthPeakW) / 1000
              ).toFixed(2),
            })}
          </div>`
        : nothing;

    return html`<div class="window">
      <div class="section-label">${this._t("peak.window_label")}</div>
      ${renderPeakBar(data, { left, right })}
      <div class="scale">
        <span>${this._t("peak.soft")} ${(data.effectiveSoftW / 1000).toFixed(1)}</span>
        <span>${this._t("peak.target")} ${(data.effectiveTargetW / 1000).toFixed(1)}</span>
        <span>${this._t("peak.hard")} ${(data.effectiveHardW / 1000).toFixed(1)}</span>
      </div>
      ${allowance}
      ${data.degraded ? html`<div class="note warn">${this._t("peak.degraded")}</div>` : nothing}
      ${stateObj?.attributes?.enabled === false
        ? html`<div class="note">${this._t("peak.off")}</div>`
        : nothing}
    </div>`;
  }

  /** The brain's own plain-language line, localized from its reason key. */
  private _renderWhy(ent: ResolvedEntities): TemplateResult | typeof nothing {
    const status = this._stateObj(ent.peak_status);
    if (!status) return nothing;
    const key = status.attributes?.reason_key as string | undefined;
    const raw = status.state && status.state !== "unknown" ? status.state : "—";
    let text: string = raw;
    if (key) {
      const params = (status.attributes?.reason_params ?? {}) as Record<string, string>;
      const localized = this._t(`reason.${key}`, params);
      if (localized !== `reason.${key}`) text = localized;
    }
    return html`<div class="why">${text}</div>`;
  }

  // --- What set the peak: the completed quarter-hours behind us -----------------
  private _renderRecent(ent: ResolvedEntities): TemplateResult {
    const stateObj = this._stateObj(ent.peak_window_power);
    const history = (stateObj?.attributes?.history ?? []) as [string, number][];
    const data = readPeakBar(stateObj);
    if (!history.length || !data) {
      return html`<div class="recent">
        <div class="section-label">${this._t("peak.recent")}</div>
        <div class="note">${this._t("peak.recent_none")}</div>
      </div>`;
    }

    const shown = history.slice(-8);
    const scale = Math.max(data.effectiveHardW * 1.25, ...shown.map(([, w]) => w), 1);
    const monthPeak = num(this._stateObj(ent.monthly_peak)?.state);

    return html`<div class="recent">
      <div class="section-label">${this._t("peak.recent")}</div>
      <div class="bars">
        ${shown.map(([stamp, watts]) => {
          const tone =
            watts >= data.effectiveHardW
              ? "hard"
              : watts >= data.effectiveSoftW
                ? "soft"
                : "ok";
          const record = !Number.isNaN(monthPeak) && watts >= monthPeak && monthPeak > 0;
          return html`<div class="bar-col" title="${(watts / 1000).toFixed(2)} kW">
            <div class="bar-slot">
              <div
                class="bar ${tone} ${record ? "record" : ""}"
                style="height:${Math.max(2, (watts / scale) * 100)}%"
              ></div>
            </div>
            <span class="bar-time">${this._fmtTime(stamp)}</span>
          </div>`;
        })}
      </div>
    </div>`;
  }

  // --- Cheap hours ahead, and how deep we intend to buy -------------------------
  private _renderBuying(ent: ResolvedEntities): TemplateResult | typeof nothing {
    const price = this._stateObj(ent.price_forecast);
    const status = this._stateObj(ent.peak_status);
    if (!price) return nothing;

    const slots = (price.attributes?.slots ?? []) as { start: string; price: number }[];
    const threshold = num(
      price.attributes?.cheap_price ?? this._stateObj(ent.cheap_price)?.state,
    );

    const upcoming = slots
      .map((slot) => ({ start: Date.parse(slot.start), price: Number(slot.price) }))
      .filter((slot) => !Number.isNaN(slot.start) && slot.start + HOUR_MS > this._now)
      .slice(0, 24);

    if (!upcoming.length || Number.isNaN(threshold)) {
      return html`<div class="buying">
        <div class="section-label">${this._t("peak.forecast")}</div>
        <div class="note">${this._t("peak.forecast_none")}</div>
      </div>`;
    }

    const max = Math.max(...upcoming.map((slot) => slot.price), threshold);
    const min = Math.min(...upcoming.map((slot) => slot.price), 0);
    const span = max - min || 1;

    // How deep this evening's buying will go, and why — the forecast's effect is
    // otherwise invisible, which makes it look arbitrary.
    const bright = ent.bright_day_target_soc
      ? num(this._stateObj(ent.bright_day_target_soc)?.state)
      : NaN;
    const dark = ent.dark_day_target_soc
      ? num(this._stateObj(ent.dark_day_target_soc)?.state)
      : NaN;
    const params = (status?.attributes?.reason_params ?? {}) as Record<string, string>;
    const activeTarget = num(params.target);
    const isBright = !Number.isNaN(activeTarget) && activeTarget === bright && bright !== dark;
    const target = Number.isNaN(activeTarget) ? dark : activeTarget;

    return html`<div class="buying">
      <div class="section-label">${this._t("peak.forecast")}</div>
      <div class="pricebars">
        ${upcoming.map((slot) => {
          const cheap = slot.price <= threshold;
          const now = slot.start <= this._now && slot.start + HOUR_MS > this._now;
          return html`<div
            class="pricebar ${cheap ? "cheap" : ""} ${now ? "now" : ""}"
            style="height:${Math.max(3, ((slot.price - min) / span) * 100)}%"
            title="${new Date(slot.start).getHours()}:00 — ${slot.price}"
          ></div>`;
        })}
      </div>
      ${Number.isNaN(target)
        ? nothing
        : html`<div class="note">
            ${this._t("peak.buying_to", { target: String(Math.round(target)) })} ·
            ${this._t(isBright ? "peak.bright" : "peak.dark")}
          </div>`}
    </div>`;
  }

  // --- Settings -----------------------------------------------------------------
  private _renderSettings(ent: ResolvedEntities): TemplateResult {
    const row = (id: string | undefined) =>
      id
        ? html`<div class="setting">
            <span class="setting-name">${this._friendlyName(id)}</span>
            <ha-entity-toggle
              .hass=${this.hass}
              .stateObj=${this._stateObj(id)}
            ></ha-entity-toggle>
          </div>`
        : nothing;

    // A plain <input>, not `ha-textfield`: HA loads that component lazily, and on a
    // dashboard it is never registered — the tag then stays un-upgraded and renders
    // as a 0 px-tall nothing, leaving every number row looking empty. The card styles
    // the input itself, so it works in every context (dashboard, preview, editor).
    const numberRow = (id: string | undefined) => {
      const stateObj = id ? this._stateObj(id) : undefined;
      if (!id || !stateObj) return nothing;
      const attrs = stateObj.attributes ?? {};
      const unit = attrs.unit_of_measurement as string | undefined;
      const unavailable = stateObj.state === "unavailable" || stateObj.state === "unknown";
      return html`<div class="setting">
        <span class="setting-name">${this._friendlyName(id)}</span>
        <span class="numfield">
          <input
            type="number"
            inputmode="decimal"
            .value=${unavailable ? "" : stateObj.state}
            step=${num(attrs.step) || 1}
            min=${ifDefined(bound(attrs.min))}
            max=${ifDefined(bound(attrs.max))}
            ?disabled=${unavailable}
            aria-label=${this._friendlyName(id)}
            @change=${(ev: Event) => this._setNumber(id, ev)}
          />
          ${unit ? html`<span class="unit">${unit}</span>` : nothing}
        </span>
      </div>`;
    };

    return html`<div class="settings">
      <div class="section-label">${this._t("peak.settings")}</div>
      ${row(ent.peak_guard)} ${row(ent.peak_follow_month)} ${row(ent.grid_charge)}
      <div class="group-label">${this._t("peak.limits")}</div>
      ${numberRow(ent.peak_soft_limit)} ${numberRow(ent.peak_target_limit)}
      ${numberRow(ent.peak_hard_limit)} ${numberRow(ent.peak_month_buffer)}
      <div class="group-label">${this._t("peak.battery")}</div>
      ${numberRow(ent.shaving_reserve_soc)} ${numberRow(ent.peak_min_soc)}
      ${numberRow(ent.peak_ready_soc)}
      <div class="group-label">${this._t("peak.cheap")}</div>
      ${numberRow(ent.grid_setpoint)} ${numberRow(ent.cheap_charge_power)}
      ${numberRow(ent.bright_day_target_soc)} ${numberRow(ent.dark_day_target_soc)}
      ${ent.stock_up || ent.stock_up_target_soc
        ? html`<div class="group-label">${this._t("peak.stockUp")}</div>
            ${row(ent.stock_up)} ${numberRow(ent.stock_up_target_soc)}`
        : nothing}
      ${ent.reset_monthly_peak
        ? html`<div class="setting">
            <span class="setting-name">${this._friendlyName(ent.reset_monthly_peak)}</span>
            <ha-icon-button
              .path=${"M12,5V1L7,6L12,11V7A6,6 0 0,1 18,13A6,6 0 0,1 12,19A6,6 0 0,1 6,13H4A8,8 0 0,0 12,21A8,8 0 0,0 20,13A8,8 0 0,0 12,5Z"}
              @click=${() => this._press(ent.reset_monthly_peak!)}
            ></ha-icon-button>
          </div>`
        : nothing}
    </div>`;
  }

  private _friendlyName(id: string): string {
    const full = this._stateObj(id)?.attributes?.friendly_name ?? id;
    // Entity names are device-prefixed ("Wallbox Peak target"); the device name is
    // already in the card header, so strip it rather than repeat it on every row.
    const device = this._entities?.deviceId
      ? this._deviceName(this._entities.deviceId)
      : undefined;
    return device && full.startsWith(`${device} `) ? full.slice(device.length + 1) : full;
  }

  private _setNumber(id: string, ev: Event): void {
    const value = Number((ev.target as HTMLInputElement).value);
    if (Number.isNaN(value)) return;
    this.hass.callService("number", "set_value", { entity_id: id, value });
  }

  private _press(id: string): void {
    this.hass.callService("button", "press", { entity_id: id });
  }

  private _countdown(iso: unknown): number | null {
    if (typeof iso !== "string") return null;
    const ms = Date.parse(iso);
    if (Number.isNaN(ms)) return null;
    const secs = (ms - this._now) / 1000;
    return secs > 0 ? secs : null;
  }

  private _lang(): string {
    return this.hass?.locale?.language ?? this.hass?.language ?? "en";
  }

  private _fmtTime(iso: string): string {
    const ms = Date.parse(iso);
    if (Number.isNaN(ms)) return "";
    return new Intl.DateTimeFormat(this._lang(), {
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(ms));
  }

  private _fmtDate(iso: string): string {
    const ms = Date.parse(iso);
    if (Number.isNaN(ms)) return "";
    return new Intl.DateTimeFormat(this._lang(), {
      day: "numeric",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(ms));
  }

  static styles = [
    peakBarStyles,
    css`
      :host {
        --goe-battery: var(--success-color, #3f9e68);
        --goe-accent: var(--primary-color);
      }
      ha-card {
        overflow: hidden;
      }
      .hacard {
        display: flex;
        flex-direction: column;
        gap: 14px;
        padding: 14px 16px 16px;
      }
      .empty {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
        padding: 24px 16px;
        text-align: center;
        color: var(--secondary-text-color);
      }
      .empty ha-icon {
        --mdc-icon-size: 32px;
      }
      .c-head {
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .c-head ha-icon {
        --mdc-icon-size: 20px;
        color: var(--goe-accent);
      }
      .title {
        font-weight: 600;
      }
      .section-label,
      .group-label {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: var(--secondary-text-color);
      }
      .group-label {
        margin-top: 6px;
      }
      .month {
        display: flex;
        flex-direction: column;
        gap: 2px;
      }
      .month-label {
        font-size: 0.76rem;
        color: var(--secondary-text-color);
      }
      .month-value {
        font-size: 2.1rem;
        font-weight: 600;
        line-height: 1.1;
        font-variant-numeric: tabular-nums;
      }
      .month-value.risk {
        color: var(--error-color, #db4437);
      }
      .month-sub {
        display: flex;
        gap: 10px;
        font-size: 0.78rem;
        color: var(--secondary-text-color);
        font-variant-numeric: tabular-nums;
      }
      .risk-note {
        display: flex;
        align-items: center;
        gap: 6px;
        margin-top: 4px;
        font-size: 0.78rem;
        color: var(--error-color, #db4437);
      }
      .risk-note ha-icon {
        --mdc-icon-size: 16px;
      }
      .window,
      .recent,
      .buying,
      .settings {
        display: flex;
        flex-direction: column;
        gap: 6px;
      }
      .scale {
        display: flex;
        justify-content: space-between;
        font-size: 0.7rem;
        color: var(--secondary-text-color);
        font-variant-numeric: tabular-nums;
      }
      .why {
        font-size: 0.85rem;
        color: var(--primary-text-color);
      }
      .note {
        font-size: 0.74rem;
        color: var(--secondary-text-color);
      }
      .note.warn {
        color: var(--warning-color, #c05252);
      }
      .bars,
      .pricebars {
        display: flex;
        align-items: flex-end;
        gap: 3px;
        height: 64px;
      }
      .bar-col {
        display: flex;
        flex: 1;
        flex-direction: column;
        align-items: center;
        gap: 3px;
        height: 100%;
      }
      .bar-slot {
        display: flex;
        align-items: flex-end;
        width: 100%;
        flex: 1;
      }
      .bar {
        width: 100%;
        border-radius: 3px 3px 0 0;
        background: var(--goe-battery);
      }
      .bar.soft {
        background: var(--warning-color, #c05252);
      }
      .bar.hard {
        background: var(--error-color, #db4437);
      }
      .bar.record {
        outline: 1px solid var(--primary-text-color);
        outline-offset: 1px;
      }
      .bar-time {
        font-size: 0.62rem;
        color: var(--secondary-text-color);
        font-variant-numeric: tabular-nums;
      }
      .pricebar {
        flex: 1;
        border-radius: 2px 2px 0 0;
        background: var(--divider-color);
      }
      .pricebar.cheap {
        background: var(--goe-battery);
      }
      .pricebar.now {
        outline: 1px solid var(--goe-accent);
        outline-offset: 1px;
      }
      .settings {
        border-top: 1px solid var(--divider-color);
        padding-top: 10px;
      }
      .setting {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        min-height: 32px;
      }
      .setting-name {
        font-size: 0.82rem;
      }
      .numfield {
        display: flex;
        align-items: center;
        gap: 4px;
        flex: 0 0 auto;
        padding: 2px 8px;
        border: 1px solid var(--divider-color);
        border-radius: 8px;
        background: var(--card-background-color, transparent);
      }
      .numfield:focus-within {
        border-color: var(--goe-accent);
      }
      .numfield input {
        width: 62px;
        border: none;
        padding: 4px 0;
        background: none;
        color: var(--primary-text-color);
        font: inherit;
        font-size: 0.86rem;
        text-align: right;
        font-variant-numeric: tabular-nums;
      }
      .numfield input:focus {
        outline: none;
      }
      .numfield input:disabled {
        color: var(--disabled-text-color, var(--secondary-text-color));
      }
      /* The spinners steal width and misfire on touch; the keyboard still steps. */
      .numfield input::-webkit-outer-spin-button,
      .numfield input::-webkit-inner-spin-button {
        margin: 0;
        -webkit-appearance: none;
      }
      .numfield input[type="number"] {
        -moz-appearance: textfield;
        appearance: textfield;
      }
      .unit {
        font-size: 0.76rem;
        color: var(--secondary-text-color);
      }
      :focus-visible {
        outline: 2px solid var(--goe-accent);
        outline-offset: 2px;
      }
    `,
  ];
}

// Register in the card picker.
(window as any).customCards = (window as any).customCards || [];
(window as any).customCards.push({
  type: "goe-steve-peak-card",
  name: "go-e + SteVe Peak protection",
  description:
    "This month's billed peak, the live billing quarter-hour against its limits, what set the peak, and the settings behind it.",
  preview: true,
  documentationURL: "https://github.com/JustChr/HAgoe_steve",
});
