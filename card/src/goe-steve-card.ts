import { LitElement, html, css, svg, nothing, type TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import "./goe-steve-card-editor";
import "./goe-steve-price-card";
import {
  resolveEntities,
  findDevices,
  PLATFORM,
  type ResolvedEntities,
} from "./entities";
import { localize } from "./localize";

/** Display name of the integration, used in the empty-state message. */
const INTEGRATION_NAME = "go-e + SteVe Smart Charging";

/** Data older than this (seconds) flips the live dot to "updated Ns ago". */
const STALE_AFTER_S = 45;

/** Volts per phase assumed when deriving actual amps from car power. */
const ASSUMED_VOLTAGE = 230;

/** Minimal shape of the bits of `hass` we touch — avoids pulling HA's types. */
interface HassEntity {
  entity_id: string;
  state: string;
  attributes: Record<string, any>;
  last_updated?: string;
}
interface Hass {
  states: Record<string, HassEntity>;
  entities: Record<string, { entity_id: string; device_id?: string; platform?: string; translation_key?: string }>;
  devices: Record<string, { name?: string; name_by_user?: string }>;
  localize: (key: string) => string;
  language?: string;
  locale?: { language?: string };
  callService: (domain: string, service: string, data: Record<string, any>) => Promise<unknown>;
  formatEntityState?: (stateObj: HassEntity, state?: string) => string;
}

export interface GoeSteveCardConfig {
  type: string;
  device?: string;
  title?: string;
  show_flow?: boolean;
  show_controls?: boolean;
  show_sessions?: boolean;
  /** Wall-dashboard preset: hides the controls block for a read-only card. */
  compact?: boolean;
}

const fmtPower = (w: number | null | undefined): string => {
  if (w === null || w === undefined || Number.isNaN(w)) return "—";
  const abs = Math.abs(w);
  if (abs >= 1000) return `${(w / 1000).toFixed(abs >= 10000 ? 0 : 1)} kW`;
  return `${Math.round(w)} W`;
};

/** kW with one decimal (the hero + balance line all speak kW). */
const fmtKw = (w: number | null | undefined): string => {
  if (w === null || w === undefined || Number.isNaN(w)) return "—";
  return `${(w / 1000).toFixed(1)} kW`;
};

/** Seconds → "1:23" / "1:02:03" for durations and countdowns. */
const fmtClock = (secs: number): string => {
  const s = Math.max(0, Math.round(secs));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const ss = s % 60;
  return (h ? `${h}:${String(m).padStart(2, "0")}` : `${m}`) + `:${String(ss).padStart(2, "0")}`;
};

const num = (v: unknown): number => {
  const n = Number(v);
  return Number.isNaN(n) ? NaN : n;
};

@customElement("goe-steve-card")
export class GoeSteveCard extends LitElement {
  @property({ attribute: false }) public hass!: Hass;
  @state() private _config!: GoeSteveCardConfig;

  /** Wall-clock tick so durations/countdowns/freshness advance every second
   *  card-side, with no entity roundtrip (concept freshness fix 4). */
  @state() private _now = Date.now();
  private _timer?: number;

  /** Optimistic control state: a tapped mode/toggle highlights immediately and
   *  is trusted until the entity confirms (or a short timeout elapses). */
  @state() private _optimistic = new Map<string, { value: string; at: number }>();

  public static getConfigElement(): HTMLElement {
    return document.createElement("goe-steve-card-editor");
  }

  public static getStubConfig(hass: Hass): GoeSteveCardConfig {
    const devices = findDevices(hass);
    return { type: "custom:goe-steve-card", device: devices[0]?.id };
  }

  public setConfig(config: GoeSteveCardConfig): void {
    this._config = {
      show_flow: true,
      show_controls: true,
      show_sessions: true,
      compact: false,
      ...config,
    };
  }

  public getCardSize(): number {
    return 8;
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

  private get _entities(): ResolvedEntities | null {
    if (!this.hass) return null;
    return resolveEntities(this.hass, this._config?.device);
  }

  /** Translate a card-chrome string in the user's language. */
  private _t(key: string, params: Record<string, string> = {}): string {
    return localize(this.hass, key, params);
  }

  protected render(): TemplateResult | typeof nothing {
    if (!this.hass || !this._config) return nothing;

    const ent = this._entities;
    if (!ent || !ent.deviceId) {
      return html`<ha-card>
        <div class="empty">
          <ha-icon icon="mdi:ev-station"></ha-icon>
          <p>${this._renderNoDevice()}</p>
        </div>
      </ha-card>`;
    }

    const title =
      this._config.title ??
      this._deviceName(ent.deviceId) ??
      this._t("card.default_title");
    const controls = this._config.show_controls && !this._config.compact;

    return html`<ha-card>
      <div class="hacard">
        ${this._renderHead(ent, title)}
        ${this._renderHero(ent)}
        ${this._renderWhy(ent)}
        ${this._config.show_flow ? this._renderSplit(ent) : nothing}
        ${this._renderChips(ent)}
        ${this._renderPlan(ent)}
        ${controls ? this._renderControls(ent) : nothing}
        ${this._config.show_sessions ? this._renderSession(ent) : nothing}
      </div>
    </ha-card>`;
  }

  /** Empty-state sentence with the integration name rendered in bold. */
  private _renderNoDevice(): TemplateResult {
    const [before, after] = this._t("card.no_device").split("{name}");
    return html`${before}<b>${INTEGRATION_NAME}</b>${after ?? ""}`;
  }

  // --- Header: brain icon, title, always-on liveness dot -----------------------
  private _renderHead(ent: ResolvedEntities, title: string): TemplateResult {
    const status = this._stateObj(ent.status);
    const controlling = this._isOn(ent.controlling);
    const age = this._ageSeconds(status ?? this._stateObj(ent.power_flow));
    const stale = age !== null && age > STALE_AFTER_S;
    const liveText = stale
      ? this._t("live.updated_ago", { ago: this._fmtAgo(age!) })
      : this._t("live.live");

    const brainLabel = controlling
      ? this._t("control.smart_active")
      : this._t("control.smart_inactive");
    return html`<div class="c-head">
      <ha-icon
        class="brain ${controlling ? "" : "off"}"
        icon="mdi:brain"
        title=${brainLabel}
        aria-label=${brainLabel}
      ></ha-icon>
      <span class="c-title">${title}</span>
      <span class="livedot ${stale ? "stale" : ""}"><i></i>${liveText}</span>
    </div>`;
  }

  // --- Hero: big live power + ring source split + subline ----------------------
  private _renderHero(ent: ResolvedEntities): TemplateResult {
    const flow = this._stateObj(ent.power_flow)?.attributes ?? {};
    const status = this._stateObj(ent.status)?.attributes ?? {};
    const carW = num(flow.car_w);
    const charging = status.charging === true || carW > 50;
    const connected = flow.car_connected;
    const phases = num(flow.phases);
    const split = this._sourceShares(flow);

    const C = 2 * Math.PI * 44;
    let acc = 0;
    const arc = (share: number, color: string) => {
      const seg = svg`<circle
        cx="50" cy="50" r="44" stroke="${color}"
        style="stroke-dasharray:${Math.max(share, 0) * C} ${C};
               stroke-dashoffset:${-acc * C};
               opacity:${share > 0 ? 1 : 0}"></circle>`;
      acc += Math.max(share, 0);
      return seg;
    };

    const solarPct =
      split.total > 0 ? Math.round((split.solar / split.total) * 100) : 0;
    const targetA = num(status.target_current_a);
    const actualA = charging && phases > 0 ? carW / (phases * ASSUMED_VOLTAGE) : NaN;
    const sub = this._heroSub(connected, charging, phases, targetA, actualA);

    return html`<div class="c-hero">
      <div class="ringwrap">
        <div class="ring ${charging ? "on" : ""}">
          <svg viewBox="0 0 100 100" fill="none" stroke-width="7" stroke-linecap="round">
            <circle class="track" cx="50" cy="50" r="44"></circle>
            ${arc(split.total ? split.grid / split.total : 0, "var(--goe-grid)")}
            ${arc(split.total ? split.battery / split.total : 0, "var(--goe-battery)")}
            ${arc(split.total ? split.solar / split.total : 0, "var(--goe-solar)")}
          </svg>
          <div class="caric">
            <ha-icon icon="${connected === false ? "mdi:car-off" : "mdi:car-electric"}"></ha-icon>
          </div>
        </div>
        ${charging && split.total > 0
          ? html`<div class="solarbadge">
              <ha-icon icon="mdi:solar-power"></ha-icon>${this._t("hero.solar_share", {
                pct: String(solarPct),
              })}
            </div>`
          : nothing}
      </div>
      <div class="heroright">
        <div class="power">
          ${Number.isNaN(carW) ? "—" : (carW / 1000).toFixed(1)} <small>kW</small>
        </div>
        <div class="herosub">${sub}</div>
      </div>
    </div>`;
  }

  private _heroSub(
    connected: unknown,
    charging: boolean,
    phases: number,
    targetA: number,
    actualA: number,
  ): string {
    if (connected === false) return this._t("hero.not_connected");
    if (!charging)
      return phases > 0
        ? this._t("hero.paused_ready", { phases: String(phases) })
        : this._t("hero.paused");
    const parts: string[] = [];
    // Show the brain's target amps, and flag when the car actually takes less
    // (a car-side limit or a failed write) — a fact two sensors held but never
    // compared.
    if (!Number.isNaN(actualA) && !Number.isNaN(targetA) && Math.abs(targetA - actualA) >= 1.5) {
      parts.push(this._t("hero.asked_takes", {
        asked: String(Math.round(targetA)),
        takes: String(Math.round(actualA)),
      }));
    } else if (!Number.isNaN(targetA) && targetA > 0) {
      parts.push(`${Math.round(targetA)} A`);
    } else if (!Number.isNaN(actualA)) {
      parts.push(`${Math.round(actualA)} A`);
    }
    if (phases > 0) parts.push(this._t("hero.phase_count", { phases: String(phases) }));
    return parts.join(" · ");
  }

  // --- The "why" line ----------------------------------------------------------
  private _renderWhy(ent: ResolvedEntities): TemplateResult {
    const status = this._stateObj(ent.status);
    return html`<div class="why">${this._statusReason(status)}</div>`;
  }

  // --- Source bar + balance line (replaces the old node diagram) ---------------
  private _renderSplit(ent: ResolvedEntities): TemplateResult {
    const flow = this._stateObj(ent.power_flow)?.attributes ?? {};
    const statusA = this._stateObj(ent.status)?.attributes ?? {};
    const carW = num(flow.car_w);
    const charging = statusA.charging === true || carW > 50;
    const split = this._sourceShares(flow);
    const seg = (key: "solar" | "battery" | "grid") => {
      const share = split.total > 0 ? split[key] / split.total : 0;
      if (share <= 0.001) return nothing;
      const label = this._t(`source.${key}`);
      return html`<button
        class="seg-src ${key}"
        style="flex-grow:${Math.max(share * 100, 0.001)}"
        @click=${() => this._tapSource(key, split[key], carW)}
      >
        ${share > 0.14 ? `${label} ${Math.round(share * 100)} %` : share > 0.05 ? `${Math.round(share * 100)} %` : ""}
      </button>`;
    };

    return html`<div class="split">
      <div class="splitbar ${charging ? "flowing" : ""}">
        ${seg("solar")}${seg("battery")}${seg("grid")}
      </div>
      <div class="splitnote" id="splitnote">
        ${this._splitNote ?? this._defaultSplitNote(split.total, flow)}
      </div>
      ${this._renderBalance(ent, flow)}
    </div>`;
  }

  private _splitNote: string | null = null;
  private _tapSource(key: "solar" | "battery" | "grid", w: number, carW: number): void {
    const label = this._t(`source.${key}`);
    this._splitNote =
      w > 0
        ? this._t("source.to_car", {
            source: label,
            watts: fmtPower(w),
            total: fmtKw(carW),
          })
        : this._t("source.none", { source: label });
    this.requestUpdate();
  }
  private _defaultSplitNote(total: number, flow: Record<string, any>): string {
    if (total > 0) return this._t("source.tap_hint");
    return flow.car_connected === false
      ? this._t("source.exporting")
      : this._t("source.paused");
  }

  private _renderBalance(ent: ResolvedEntities, flow: Record<string, any>): TemplateResult {
    const pv = num(flow.pv_w);
    const house = num(flow.house_w);
    const grid = num(flow.grid_w);
    const batt = flow.battery_w === null || flow.battery_w === undefined ? null : num(flow.battery_w);
    const soc = flow.battery_soc;
    const reserve = num(this._stateObj(ent.battery_reserve_soc)?.state);
    const hold = this._holdActive(ent);

    const items: TemplateResult[] = [];
    if (!Number.isNaN(pv))
      items.push(html`<span><i class="dot" style="background:var(--goe-solar)"></i>${this._t("balance.pv")} <b>${fmtKw(pv)}</b></span>`);
    if (!Number.isNaN(house))
      items.push(html`<span>${this._t("balance.house")} <b>${fmtKw(house)}</b></span>`);
    if (!Number.isNaN(grid))
      items.push(html`<span><i class="dot" style="background:var(--goe-grid)"></i>${grid < -50 ? this._t("balance.export") : this._t("balance.grid")} <b>${fmtKw(Math.abs(grid))}</b></span>`);
    if (batt !== null) {
      const dir = batt > 50 ? "+ " : batt < -50 ? "− " : "";
      const power = Math.abs(batt) <= 50 ? this._t("balance.idle") : `${dir}${fmtKw(Math.abs(batt))}`;
      const socTxt =
        soc != null
          ? ` · ${Math.round(num(soc))} %${Number.isNaN(reserve) ? "" : ` · ${this._t("balance.reserve", { pct: String(Math.round(reserve)) })}`}`
          : "";
      const shield = hold
        ? html`<ha-icon class="hold-ico" icon="mdi:shield"></ha-icon>`
        : nothing;
      items.push(html`<span><i class="dot" style="background:var(--goe-battery)"></i>${this._t("balance.battery")} <b>${power}</b>${socTxt}${shield}</span>`);
    }
    return html`<div class="balance">${items}</div>`;
  }

  // --- Chips: previously invisible engine facts --------------------------------
  private _renderChips(ent: ResolvedEntities): TemplateResult {
    const status = this._stateObj(ent.status)?.attributes ?? {};
    const chips: TemplateResult[] = [];

    // Battery-hold shield (the missing piece).
    if (this._holdActive(ent)) {
      const manual = (status.hold_source ?? "auto") === "hold";
      chips.push(this._chip("mdi:shield", manual ? "chip.hold_manual" : "chip.hold", {}, "hold"));
    }

    // Price verdict against the cheap threshold.
    const price = this._stateObj(ent.price_forecast);
    if (price && !["unknown", "unavailable", ""].includes(price.state)) {
      const now = num(price.state);
      const target = this._cheapTarget(ent);
      const unit = price.attributes.unit ?? "";
      if (!Number.isNaN(now)) {
        const ok = !Number.isNaN(target) && now <= target;
        chips.push(
          this._chip(
            "mdi:cash-clock",
            ok ? "chip.price_cheap" : "chip.price_wait",
            { price: this._fmtPriceNum(now), unit, target: this._fmtPriceNum(target) },
            ok ? "cheap" : "",
          ),
        );
      }
    }

    // Live dwell countdowns.
    const resume = this._countdown(status.resume_not_before);
    if (resume !== null)
      chips.push(this._chip("mdi:clock-outline", "chip.resume_in", { time: fmtClock(resume) }));
    const pause = this._countdown(status.pause_not_before);
    if (pause !== null)
      chips.push(this._chip("mdi:clock-outline", "chip.riding_out", { time: fmtClock(pause) }));

    // Forced-off explainer.
    if (status.forced === false)
      chips.push(this._chip("mdi:hand-back-left", "chip.forced_off", {}, "hold"));

    if (chips.length === 0) return html``;
    return html`<div class="chips">${chips}</div>`;
  }

  private _chip(
    icon: string,
    key: string,
    params: Record<string, string>,
    cls = "",
  ): TemplateResult {
    return html`<span class="chipx ${cls}"><ha-icon icon="${icon}"></ha-icon>${this._t(key, params)}</span>`;
  }

  // --- Plan strip: progress toward the target energy ---------------------------
  // The price forecast + draggable "cheap" threshold now live in the dedicated
  // price card, so the wallbox card keeps only the charging-progress line here.
  private _renderPlan(ent: ResolvedEntities): TemplateResult | typeof nothing {
    const mode = this._effectiveState(ent.charging_mode);
    if (mode !== "smart") return nothing;

    const status = this._stateObj(ent.status)?.attributes ?? {};
    const bookedStarts = new Set<string>(status.plan ?? []);
    const planLine = this._planLine(ent, bookedStarts.size);
    if (planLine === nothing) return nothing;

    return html`<div class="plan">${planLine}</div>`;
  }

  private _planLine(
    ent: ResolvedEntities,
    windows: number,
  ): TemplateResult | typeof nothing {
    const target = num(this._stateObj(ent.target_energy)?.state);
    if (Number.isNaN(target) || target <= 0) return nothing;
    const delivered = num((this._stateObj(ent.power_flow)?.attributes ?? {}).session_energy_kwh);
    const done = Number.isNaN(delivered) ? 0 : delivered;
    const pct = Math.min(100, Math.round((done / target) * 100));
    const track = windows >= 4 ? this._t("plan.on_track") : this._t("plan.tight");
    return html`
      <div class="planline">
        <b>${done.toFixed(1)} / ${target.toFixed(0)} kWh</b> — ${track}
      </div>
      <div class="progress"><i style="width:${pct}%"></i></div>`;
  }

  // --- Controls: segmented mode + contextual tunables + battery three-way ------
  private _renderControls(ent: ResolvedEntities): TemplateResult {
    const mode = this._stateObj(ent.charging_mode);
    const modeState = this._effectiveState(ent.charging_mode);
    const isManual = modeState === "manual";

    const hintKey = modeState ? `mode_hint.${modeState}` : "";
    const hint = hintKey ? this._t(hintKey) : "";
    return html`<div class="controls">
      ${mode ? this._renderModeSeg(ent, mode) : nothing}
      ${hint && hint !== hintKey ? html`<div class="modehint">${hint}</div>` : nothing}
      <div class="ctxctl">
        ${isManual ? this._renderManual(ent) : this._renderModeTunables(ent, modeState)}
        ${this._renderBatteryThreeWay(ent)}
        ${this._renderNumberRow(ent.battery_reserve_soc, "control.battery_reserve")}
      </div>
    </div>`;
  }

  private _renderModeSeg(ent: ResolvedEntities, mode: HassEntity): TemplateResult {
    const options: string[] = mode.attributes.options ?? [];
    const active = this._effectiveState(ent.charging_mode);
    const icons: Record<string, string> = {
      manual: "mdi:hand-back-right",
      solar: "mdi:solar-power",
      solar_min: "mdi:solar-power-variant",
      smart: "mdi:brain",
      fast: "mdi:flash",
    };
    return html`<div class="seg">
      ${options.map(
        (opt) => html`<button
          class="${opt === active ? "on" : ""}"
          @click=${() => this._selectOptimistic(mode, opt)}
        >
          <ha-icon icon="${icons[opt] ?? "mdi:ev-station"}"></ha-icon>
          <span>${this._localizeOption(mode, opt)}</span>
        </button>`,
      )}
    </div>`;
  }

  private _renderModeTunables(ent: ResolvedEntities, modeState: string | undefined): TemplateResult {
    return html`
      ${modeState === "smart"
        ? html`${this._renderNumberRow(ent.target_energy, "control.target_energy")}
            ${this._renderDateTimeRow(ent.departure, "control.departure")}`
        : nothing}
      ${modeState === "solar_min" ? this._renderNumberRow(ent.min_current, "control.min_current") : nothing}
      ${modeState === "fast" ? this._renderNumberRow(ent.max_current, "control.max_current") : nothing}
      ${ent.auto_phase
        ? html`<div class="ctlrow">
            <label>${this._t("control.auto_phase")}</label>
            <ha-switch
              .checked=${this._isOn(ent.auto_phase)}
              @change=${(e: Event) => this._toggle(ent.auto_phase, e)}
            ></ha-switch>
          </div>`
        : nothing}`;
  }

  private _renderManual(ent: ResolvedEntities): TemplateResult {
    const charging = this._isOn(ent.manual_charge);
    return html`
      ${ent.manual_charge
        ? html`<button
            class="bigbtn ${charging ? "stop" : ""}"
            @click=${() => this._toggleManualCharge(ent, charging)}
          >
            <ha-icon icon="${charging ? "mdi:stop" : "mdi:play"}"></ha-icon>
            ${charging ? this._t("action.stop_charging") : this._t("action.start_charging")}
          </button>`
        : nothing}
      ${this._renderNumberRow(ent.manual_current, "control.manual_current")}
      ${ent.manual_phases
        ? html`<div class="ctlrow">
            <label>${this._t("control.manual_phases")}</label>
            ${this._renderSelect(this._stateObj(ent.manual_phases)!)}
          </div>`
        : nothing}`;
  }

  private _renderBatteryThreeWay(ent: ResolvedEntities): TemplateResult | typeof nothing {
    const sel = this._stateObj(ent.battery_hold_mode);
    if (!sel) return nothing;
    const options: string[] = sel.attributes.options ?? ["auto", "hold", "free"];
    const active = this._effectiveState(ent.battery_hold_mode);
    const holdActive = this._holdActive(ent);
    return html`<div class="ctlrow">
      <label>${this._t("control.home_battery")}</label>
      <span class="minisg">
        ${options.map(
          (opt) => html`<button
            class="${opt === active ? "on" : ""}"
            @click=${() => this._selectOptimistic(sel, opt)}
          >
            ${this._localizeOption(sel, opt)}${opt === "auto" && holdActive && active === "auto"
              ? html`<ha-icon class="hold-ico" icon="mdi:shield"></ha-icon>`
              : nothing}
          </button>`,
        )}
      </span>
    </div>`;
  }

  private _renderNumberRow(id: string | undefined, labelKey: string): TemplateResult | typeof nothing {
    const stateObj = this._stateObj(id);
    if (!stateObj) return nothing;
    return html`<div class="ctlrow">
      <label>${this._t(labelKey)}</label>
      ${this._renderNumber(stateObj)}
    </div>`;
  }

  private _renderDateTimeRow(id: string | undefined, labelKey: string): TemplateResult | typeof nothing {
    const stateObj = this._stateObj(id);
    if (!stateObj) return nothing;
    return html`<div class="ctlrow">
      <label>${this._t(labelKey)}</label>
      ${this._renderDateTime(stateObj)}
    </div>`;
  }

  // --- Session: live-ticking duration + tag + energy, with start/stop ----------
  private _renderSession(ent: ResolvedEntities): TemplateResult | typeof nothing {
    const active = this._stateObj(ent.active_transaction);
    const picker = this._stateObj(ent.selected_tag);
    if (!active && !picker) return nothing;

    const hasActive =
      !!active && !["idle", "unknown", "unavailable", ""].includes(active.state);
    const flow = this._stateObj(ent.power_flow)?.attributes ?? {};
    const energyKwh = num(flow.session_energy_kwh);

    let meta: TemplateResult | string = "";
    if (hasActive && active) {
      const name = (active.attributes.name as string) ?? active.state;
      const dur = this._liveDuration(active.attributes.started as string | undefined);
      const parts: string[] = [];
      if (dur) parts.push(dur);
      if (!Number.isNaN(energyKwh) && energyKwh > 0) parts.push(`${energyKwh.toFixed(2)} kWh`);
      meta = html`<b>${name}</b>${parts.length ? html` · <span class="mono">${parts.join(" · ")}</span>` : nothing}`;
    }

    return html`<div class="session">
      ${this._renderTagPicker(picker, hasActive)}
      <div class="session-row">
        <ha-icon icon="mdi:card-account-details"></ha-icon>
        <span>${hasActive ? meta : this._t("session.none_hint")}</span>
      </div>
    </div>`;
  }

  private _renderTagPicker(
    picker: HassEntity | undefined,
    hasActive: boolean,
  ): TemplateResult | typeof nothing {
    if (!picker) return nothing;
    const options: string[] = picker.attributes.options ?? [];
    if (options.length === 0) return nothing;
    const hasSelection = options.includes(picker.state);
    return html`<div class="tag-picker">
      ${hasActive
        ? nothing
        : html`<div class="ctlrow">
            <label>${this._t("control.tag")}</label>
            ${this._renderSelect(picker)}
          </div>`}
      <div class="tag-actions">
        ${hasActive
          ? html`<button class="bigbtn stop" @click=${() => this._confirmStop()}>
              <ha-icon icon="mdi:stop"></ha-icon>${this._t("action.stop")}
            </button>`
          : html`<button
              class="bigbtn"
              ?disabled=${!hasSelection}
              @click=${() => this._callTagService("remote_start")}
            >
              <ha-icon icon="mdi:play"></ha-icon>${this._t("action.start")}
            </button>`}
      </div>
    </div>`;
  }

  // --- localized status reason (unchanged from before) -------------------------
  private _statusReason(status: HassEntity | undefined): TemplateResult | string {
    const raw = status?.state && status.state !== "unknown" ? status.state : "—";
    const key = status?.attributes?.reason_key as string | undefined;
    if (!key) return raw;
    const fullKey = `reason.${key}`;
    const params = (status?.attributes?.reason_params ?? {}) as Record<string, string>;
    const localized = this._t(fullKey, this._localizeNumbers(params));
    return localized === fullKey ? raw : localized;
  }

  private _localizeNumbers(params: Record<string, string>): Record<string, string> {
    const lang = (this.hass?.locale?.language || this.hass?.language || "en")
      .toLowerCase()
      .split("-")[0];
    const out: Record<string, string> = {};
    for (const [name, value] of Object.entries(params)) {
      const m = /^-?\d+(?:\.(\d+))?$/.exec(value);
      if (m) {
        const decimals = m[1]?.length ?? 0;
        out[name] = new Intl.NumberFormat(lang, {
          minimumFractionDigits: decimals,
          maximumFractionDigits: decimals,
        }).format(Number(value));
      } else {
        out[name] = value;
      }
    }
    return out;
  }

  // --- control primitives ------------------------------------------------------
  private _renderNumber(stateObj: HassEntity): TemplateResult {
    const a = stateObj.attributes;
    const unit = a.unit_of_measurement ?? "";
    return html`<span class="ctl-number-wrap">
      <input
        class="ctl-number"
        type="number"
        .value=${stateObj.state}
        min=${a.min ?? nothing}
        max=${a.max ?? nothing}
        step=${a.step ?? nothing}
        @change=${(e: Event) => this._setNumber(stateObj, (e.target as HTMLInputElement).value)}
      />
      ${unit ? html`<span class="ctl-unit">${unit}</span>` : nothing}
    </span>`;
  }

  private _setNumber(stateObj: HassEntity, value: string): void {
    const n = Number(value);
    if (Number.isNaN(n) || String(n) === stateObj.state) return;
    this.hass.callService("number", "set_value", { entity_id: stateObj.entity_id, value: n });
  }

  private _renderDateTime(stateObj: HassEntity): TemplateResult {
    return html`<input
      class="ctl-datetime"
      type="datetime-local"
      .value=${this._toLocalInput(stateObj.state)}
      @change=${(e: Event) => this._setDateTime(stateObj, (e.target as HTMLInputElement).value)}
    />`;
  }

  private _toLocalInput(iso: string): string {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return "";
    const pad = (n: number) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
  }

  private _setDateTime(stateObj: HassEntity, value: string): void {
    if (!value) return;
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return;
    this.hass.callService("datetime", "set_value", {
      entity_id: stateObj.entity_id,
      datetime: d.toISOString(),
    });
  }

  private _renderSelect(stateObj: HassEntity): TemplateResult {
    const options: string[] = stateObj.attributes.options ?? [];
    return html`<select
      class="ctl-select"
      @change=${(e: Event) => this._selectOption(stateObj, (e.target as HTMLSelectElement).value)}
    >
      ${options.map(
        (opt) => html`<option .value=${opt} ?selected=${opt === stateObj.state}>
          ${this._localizeOption(stateObj, opt)}
        </option>`,
      )}
    </select>`;
  }

  // --- SteVe session actions ---------------------------------------------------
  private _callTagService(service: string): void {
    this.hass.callService(PLATFORM, service, {});
  }
  private _confirmStop(): void {
    if (window.confirm(this._t("action.stop_confirm"))) this._callTagService("remote_stop");
  }
  private _toggleManualCharge(ent: ResolvedEntities, charging: boolean): void {
    if (!ent.manual_charge) return;
    this.hass.callService("switch", charging ? "turn_off" : "turn_on", {
      entity_id: ent.manual_charge,
    });
  }

  // --- data / source helpers ---------------------------------------------------
  private _sourceShares(flow: Record<string, any>): {
    solar: number;
    battery: number;
    grid: number;
    total: number;
  } {
    const s = flow.sources ?? {};
    const solar = Math.max(0, num(s.solar_w) || 0);
    const battery = Math.max(0, num(s.battery_w) || 0);
    const grid = Math.max(0, num(s.grid_w) || 0);
    return { solar, battery, grid, total: solar + battery + grid };
  }

  /** The active cheap-price target (from the forecast attr or the number entity). */
  private _cheapTarget(ent: ResolvedEntities): number {
    const price = this._stateObj(ent.price_forecast);
    const fromAttr = num(price?.attributes?.cheap_price);
    if (!Number.isNaN(fromAttr)) return fromAttr;
    return num(this._stateObj(ent.cheap_price)?.state);
  }

  /** True when the home battery is currently held (from status or the sensor). */
  private _holdActive(ent: ResolvedEntities): boolean {
    const fromStatus = (this._stateObj(ent.status)?.attributes ?? {}).hold_battery;
    if (typeof fromStatus === "boolean") return fromStatus;
    return this._isOn(ent.battery_hold);
  }

  /** Seconds remaining until an ISO deadline, or null when past/absent. */
  private _countdown(iso: unknown): number | null {
    if (typeof iso !== "string") return null;
    const ms = Date.parse(iso);
    if (Number.isNaN(ms)) return null;
    const secs = (ms - this._now) / 1000;
    return secs > 0 ? secs : null;
  }

  private _ageSeconds(stateObj: HassEntity | undefined): number | null {
    if (!stateObj?.last_updated) return null;
    const ms = Date.parse(stateObj.last_updated);
    if (Number.isNaN(ms)) return null;
    return Math.max(0, (this._now - ms) / 1000);
  }
  private _fmtAgo(secs: number): string {
    if (secs < 90) return `${Math.round(secs)} s`;
    return `${Math.round(secs / 60)} min`;
  }

  private _liveDuration(started: string | undefined): string {
    if (!started) return "";
    const start = Date.parse(started);
    if (Number.isNaN(start)) return "";
    return fmtClock((this._now - start) / 1000);
  }

  private _fmtPriceNum(v: number): string {
    if (Number.isNaN(v)) return "—";
    // Whole numbers (ct/kWh) stay tidy; fractional (€/kWh) keep 2 decimals.
    return Number.isInteger(v) ? String(v) : v.toFixed(v < 1 ? 2 : 1);
  }

  // --- optimistic control state ------------------------------------------------
  /** Reflect a select's state, trusting a recent tap until the entity confirms. */
  private _effectiveState(id: string | undefined): string | undefined {
    const real = this._stateObj(id)?.state;
    if (!id) return real;
    const opt = this._optimistic.get(id);
    if (!opt) return real;
    // Confirmed, or timed out after 4 s → drop the optimistic value.
    if (real === opt.value || Date.now() - opt.at > 4000) {
      this._optimistic.delete(id);
      return real;
    }
    return opt.value;
  }
  private _selectOptimistic(stateObj: HassEntity, option: string): void {
    if (option === stateObj.state) return;
    this._optimistic.set(stateObj.entity_id, { value: option, at: Date.now() });
    this.requestUpdate();
    this.hass.callService("select", "select_option", {
      entity_id: stateObj.entity_id,
      option,
    });
  }

  // --- hass helpers ------------------------------------------------------------
  private _stateObj(id?: string): HassEntity | undefined {
    return id ? this.hass.states[id] : undefined;
  }
  private _isOn(id?: string): boolean {
    return this._stateObj(id)?.state === "on";
  }
  private _localizeOption(s: HassEntity, opt: string): string {
    const tk = this.hass.entities?.[s.entity_id]?.translation_key;
    if (tk) {
      const key = `component.${PLATFORM}.entity.select.${tk}.state.${opt}`;
      const label = this.hass.localize?.(key);
      if (label) return label;
    }
    if (this.hass.formatEntityState) {
      const label = this.hass.formatEntityState({ ...s, state: opt }, opt);
      if (label) return label;
    }
    return opt;
  }
  private _deviceName(deviceId: string): string | null {
    const d = this.hass.devices[deviceId];
    return d?.name_by_user || d?.name || null;
  }
  private _selectOption(stateObj: HassEntity, option: string): void {
    if (option === stateObj.state) return;
    this.hass.callService("select", "select_option", { entity_id: stateObj.entity_id, option });
  }
  private _toggle(id: string | undefined, e: Event): void {
    if (!id) return;
    const on = (e.target as HTMLInputElement).checked;
    this.hass.callService("switch", on ? "turn_on" : "turn_off", { entity_id: id });
  }

  static styles = css`
    :host {
      --goe-solar: #dd9a16;
      --goe-battery: var(--success-color, #3f9e68);
      --goe-grid: #67789c;
      --goe-accent: var(--primary-color);
      --goe-chip: var(--secondary-background-color);
    }
    ha-card {
      overflow: hidden;
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
    .mono {
      font-variant-numeric: tabular-nums;
    }
    .hacard {
      display: flex;
      flex-direction: column;
      gap: 14px;
      padding: 14px 16px 16px;
    }

    /* Header */
    .c-head {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .c-title {
      font-weight: 600;
      font-size: 1.05rem;
    }
    .brain {
      color: var(--goe-accent);
    }
    .brain.off {
      color: var(--disabled-text-color);
    }
    .livedot {
      margin-left: auto;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 0.72rem;
      color: var(--secondary-text-color);
    }
    .livedot i {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--goe-battery);
    }
    .livedot.stale i {
      background: var(--disabled-text-color);
    }
    @media (prefers-reduced-motion: no-preference) {
      .livedot:not(.stale) i {
        animation: pulse 2s ease-in-out infinite;
      }
      @keyframes pulse {
        50% {
          opacity: 0.35;
        }
      }
    }

    /* Hero */
    .c-hero {
      display: flex;
      align-items: center;
      gap: 16px;
    }
    .ringwrap {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 5px;
      flex: none;
    }
    .ring {
      width: 92px;
      height: 92px;
      flex: none;
      position: relative;
    }
    .solarbadge {
      display: inline-flex;
      align-items: center;
      gap: 3px;
      font-size: 0.72rem;
      font-weight: 600;
      color: var(--goe-solar);
      font-variant-numeric: tabular-nums;
    }
    .solarbadge ha-icon {
      --mdc-icon-size: 14px;
    }
    .ring svg {
      width: 100%;
      height: 100%;
      transform: rotate(-90deg);
    }
    .ring .track {
      stroke: var(--divider-color);
    }
    .ring circle {
      transition: stroke-dasharray 0.5s ease, stroke-dashoffset 0.5s ease;
    }
    .caric {
      position: absolute;
      inset: 0;
      display: grid;
      place-items: center;
    }
    .caric ha-icon {
      --mdc-icon-size: 34px;
      color: var(--secondary-text-color);
    }
    .ring.on .caric ha-icon {
      color: var(--primary-text-color);
    }
    .power {
      font-size: 2.1rem;
      font-weight: 600;
      line-height: 1;
      font-variant-numeric: tabular-nums;
    }
    .power small {
      font-size: 1.05rem;
      font-weight: 500;
      color: var(--secondary-text-color);
    }
    .herosub {
      color: var(--secondary-text-color);
      font-size: 0.85rem;
      margin-top: 5px;
      font-variant-numeric: tabular-nums;
    }

    .why {
      font-size: 0.9rem;
      color: var(--primary-text-color);
      min-height: 1.2em;
    }
    .why b {
      color: var(--goe-accent);
    }

    /* Source bar + balance */
    .splitbar {
      display: flex;
      height: 26px;
      border-radius: 8px;
      overflow: hidden;
      gap: 2px;
      background: var(--goe-chip);
    }
    .seg-src {
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      font-size: 0.72rem;
      font-weight: 600;
      min-width: 0;
      overflow: hidden;
      white-space: nowrap;
      border: 0;
      cursor: pointer;
      padding: 0;
      font-family: inherit;
      transition: flex-grow 0.6s ease;
    }
    .seg-src.solar {
      background: var(--goe-solar);
    }
    .seg-src.battery {
      background: var(--goe-battery);
    }
    .seg-src.grid {
      background: var(--goe-grid);
    }
    @media (prefers-reduced-motion: no-preference) {
      .splitbar.flowing .seg-src {
        background-image: linear-gradient(
          100deg,
          rgba(255, 255, 255, 0) 40%,
          rgba(255, 255, 255, 0.28) 50%,
          rgba(255, 255, 255, 0) 60%
        );
        background-size: 220% 100%;
        animation: sheen 2.6s linear infinite;
      }
      @keyframes sheen {
        from {
          background-position: 130% 0;
        }
        to {
          background-position: -90% 0;
        }
      }
    }
    .splitnote {
      font-size: 0.74rem;
      color: var(--secondary-text-color);
      margin-top: 6px;
      min-height: 1.1em;
      font-variant-numeric: tabular-nums;
    }
    .balance {
      display: flex;
      flex-wrap: wrap;
      gap: 4px 14px;
      margin-top: 4px;
      font-size: 0.78rem;
      color: var(--secondary-text-color);
      font-variant-numeric: tabular-nums;
    }
    .balance b {
      color: var(--primary-text-color);
    }
    .balance .dot {
      width: 8px;
      height: 8px;
      border-radius: 3px;
      display: inline-block;
      margin-right: 5px;
    }
    .hold-ico {
      --mdc-icon-size: 14px;
      color: var(--warning-color, #c05252);
      margin-left: 4px;
      vertical-align: -2px;
    }

    /* Chips */
    .chips {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .chipx {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: var(--goe-chip);
      border-radius: 999px;
      padding: 4px 11px;
      font-size: 0.76rem;
      font-weight: 500;
      color: var(--primary-text-color);
      border: 1px solid transparent;
      font-variant-numeric: tabular-nums;
    }
    .chipx ha-icon {
      --mdc-icon-size: 15px;
      color: var(--secondary-text-color);
    }
    .chipx.hold {
      border-color: var(--warning-color, #c05252);
      color: var(--warning-color, #c05252);
    }
    .chipx.hold ha-icon {
      color: var(--warning-color, #c05252);
    }
    .chipx.cheap {
      border-color: var(--goe-battery);
    }
    .chipx.cheap ha-icon {
      color: var(--goe-battery);
    }

    /* Plan strip: charging-progress line */
    .planline {
      font-size: 0.78rem;
      color: var(--secondary-text-color);
      margin-top: 6px;
      font-variant-numeric: tabular-nums;
    }
    .planline b {
      color: var(--primary-text-color);
    }
    .progress {
      height: 5px;
      border-radius: 999px;
      background: var(--goe-chip);
      margin-top: 6px;
      overflow: hidden;
    }
    .progress i {
      display: block;
      height: 100%;
      background: var(--goe-accent);
      border-radius: 999px;
      transition: width 0.5s ease;
    }

    /* Controls */
    .controls {
      border-top: 1px solid var(--divider-color);
      padding-top: 12px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .ctxctl {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .seg {
      display: flex;
      background: var(--goe-chip);
      border-radius: 12px;
      padding: 3px;
      gap: 2px;
    }
    .seg button {
      flex: 1;
      border: 0;
      background: transparent;
      border-radius: 9px;
      padding: 7px 2px 5px;
      cursor: pointer;
      color: var(--secondary-text-color);
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 2px;
      font-family: inherit;
      font-size: 0.64rem;
      font-weight: 600;
    }
    .seg button ha-icon {
      --mdc-icon-size: 17px;
    }
    .seg button.on {
      background: var(--card-background-color);
      color: var(--goe-accent);
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
    }
    .modehint {
      font-size: 0.78rem;
      color: var(--secondary-text-color);
      margin-top: -2px;
    }
    .ctlrow {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .ctlrow label {
      font-size: 0.85rem;
      color: var(--secondary-text-color);
      white-space: nowrap;
    }
    .minisg {
      display: inline-flex;
      background: var(--goe-chip);
      border-radius: 10px;
      padding: 2px;
      gap: 2px;
    }
    .minisg button {
      border: 0;
      background: transparent;
      border-radius: 8px;
      padding: 5px 13px;
      font: inherit;
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--secondary-text-color);
      cursor: pointer;
    }
    .minisg button.on {
      background: var(--card-background-color);
      color: var(--goe-accent);
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
    }
    .bigbtn {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      border: 0;
      border-radius: 12px;
      padding: 12px;
      width: 100%;
      font: inherit;
      font-size: 0.92rem;
      font-weight: 600;
      cursor: pointer;
      background: var(--goe-accent);
      color: var(--text-primary-color, #fff);
    }
    .bigbtn ha-icon {
      --mdc-icon-size: 18px;
    }
    .bigbtn.stop {
      background: color-mix(in srgb, var(--error-color, #db4437) 14%, var(--card-background-color));
      color: var(--error-color, #db4437);
      border: 1px solid var(--error-color, #db4437);
    }
    .bigbtn[disabled] {
      opacity: 0.5;
      cursor: default;
    }

    /* Inputs */
    .ctl-select,
    .ctl-datetime {
      min-width: 150px;
      max-width: 60%;
      padding: 8px 10px;
      border-radius: 8px;
      border: 1px solid var(--divider-color);
      background: var(--card-background-color, var(--ha-card-background));
      color: var(--primary-text-color);
      font-family: inherit;
      font-size: 0.9rem;
      cursor: pointer;
    }
    .ctl-select:focus,
    .ctl-datetime:focus,
    .ctl-number:focus {
      outline: none;
      border-color: var(--goe-accent);
    }
    .ctl-number-wrap {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      justify-content: flex-end;
    }
    .ctl-number {
      width: 90px;
      padding: 8px 10px;
      border-radius: 8px;
      border: 1px solid var(--divider-color);
      background: var(--card-background-color, var(--ha-card-background));
      color: var(--primary-text-color);
      font-family: inherit;
      font-size: 0.9rem;
      text-align: right;
    }
    .ctl-unit {
      color: var(--secondary-text-color);
      font-size: 0.85rem;
      white-space: nowrap;
    }

    /* Session */
    .session {
      border-top: 1px solid var(--divider-color);
      padding-top: 10px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .session-row {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.85rem;
      color: var(--primary-text-color);
      font-variant-numeric: tabular-nums;
    }
    .session-row ha-icon {
      --mdc-icon-size: 16px;
      color: var(--secondary-text-color);
    }
    .tag-picker {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .tag-actions {
      display: flex;
      gap: 8px;
    }
    :focus-visible {
      outline: 2px solid var(--goe-accent);
      outline-offset: 2px;
    }
  `;
}

// Register in the card picker.
(window as any).customCards = (window as any).customCards || [];
(window as any).customCards.push({
  type: "goe-steve-card",
  name: "go-e + SteVe Smart Charging",
  description:
    "Live source split, the brain's reasoning, plan strip and inline controls for smart EV charging.",
  preview: true,
  documentationURL: "https://github.com/JustChr/HAgoe_steve",
});
