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

/** Minimal shape of the bits of `hass` we touch — avoids pulling HA's types. */
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
  formatEntityState?: (stateObj: HassEntity, state?: string) => string;
}

export interface GoeSteveCardConfig {
  type: string;
  device?: string;
  title?: string;
  show_flow?: boolean;
  show_controls?: boolean;
  show_sessions?: boolean;
}

const fmtPower = (w: number | null | undefined): string => {
  if (w === null || w === undefined || Number.isNaN(w)) return "—";
  const abs = Math.abs(w);
  if (abs >= 1000) return `${(w / 1000).toFixed(abs >= 10000 ? 0 : 1)} kW`;
  return `${Math.round(w)} W`;
};

@customElement("goe-steve-card")
export class GoeSteveCard extends LitElement {
  @property({ attribute: false }) public hass!: Hass;
  @state() private _config!: GoeSteveCardConfig;

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
      ...config,
    };
  }

  public getCardSize(): number {
    return 8;
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

    return html`<ha-card>
      ${this._renderHeader(ent, title)}
      <div class="content">
        ${this._config.show_flow ? this._renderFlow(ent) : nothing}
        ${this._config.show_controls ? this._renderLive(ent) : nothing}
        ${this._config.show_controls ? this._renderControls(ent) : nothing}
        ${this._config.show_sessions ? this._renderSessions(ent) : nothing}
      </div>
    </ha-card>`;
  }

  /** Empty-state sentence with the integration name rendered in bold. */
  private _renderNoDevice(): TemplateResult {
    const [before, after] = this._t("card.no_device").split("{name}");
    return html`${before}<b>${INTEGRATION_NAME}</b>${after ?? ""}`;
  }

  // --- Header: status reason + mode/policy chips --------------------------------
  private _renderHeader(ent: ResolvedEntities, title: string): TemplateResult {
    const status = this._stateObj(ent.status);
    const reason = this._statusReason(status);
    const controlling = this._isOn(ent.controlling);
    const mode = this._displayState(ent.charging_mode);
    const policy = this._displayState(ent.battery_policy);

    return html`<div class="header">
      <div class="title-row">
        <ha-icon class="brain ${controlling ? "active" : ""}" icon="mdi:brain"></ha-icon>
        <span class="title">${title}</span>
      </div>
      <div class="reason">${reason}</div>
      <div class="chips">
        ${mode ? html`<span class="chip"><ha-icon icon="mdi:ev-station"></ha-icon>${mode}</span>` : nothing}
        ${policy ? html`<span class="chip"><ha-icon icon="mdi:home-battery"></ha-icon>${policy}</span>` : nothing}
      </div>
    </div>`;
  }

  /**
   * Localize the status line from the sensor's structured `reason_key` +
   * `reason_params` attributes (the engine emits English in the state itself).
   * Falls back to the raw English state when the key is missing or untranslated
   * — e.g. an older integration build, or a key the card doesn't know yet.
   */
  private _statusReason(status: HassEntity | undefined): string {
    const raw =
      status?.state && status.state !== "unknown" ? status.state : "—";
    const key = status?.attributes?.reason_key as string | undefined;
    if (!key) return raw;
    const fullKey = `reason.${key}`;
    const params = (status?.attributes?.reason_params ?? {}) as Record<
      string,
      string
    >;
    const localized = this._t(fullKey, this._localizeNumbers(params));
    return localized === fullKey ? raw : localized;
  }

  /**
   * Re-render the reason params in the viewer's locale. The engine emits them as
   * machine-formatted strings (`.` decimal, no separators); we parse those back
   * and reformat with `Intl.NumberFormat` so a German user sees `0,250` and
   * `1.500`, keeping the engine's decimal precision (incl. trailing zeros).
   * Non-numeric values pass through untouched.
   */
  private _localizeNumbers(
    params: Record<string, string>,
  ): Record<string, string> {
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

  // --- Live energy-flow diagram ------------------------------------------------
  private _renderFlow(ent: ResolvedEntities): TemplateResult {
    const flow = this._stateObj(ent.power_flow);
    const a = flow?.attributes ?? {};
    const pv = Number(a.pv_w ?? NaN);
    const grid = Number(a.grid_w ?? NaN);
    const battery = a.battery_w === null || a.battery_w === undefined ? null : Number(a.battery_w);
    const car = Number(a.car_w ?? (flow ? flow.state : NaN));
    const house = Number(a.house_w ?? NaN);
    const soc = a.battery_soc;
    const connected = a.car_connected;

    // Edge "active" thresholds (W) — ignore sensor noise.
    const TH = 50;
    const node = (
      x: number,
      y: number,
      icon: string,
      label: string,
      value: string,
      extra = "",
    ) => svg`
      <g class="node" transform="translate(${x},${y})">
        <circle r="26"></circle>
        <foreignObject x="-13" y="-20" width="26" height="26">
          <ha-icon icon="${icon}"></ha-icon>
        </foreignObject>
        <text class="node-val" y="14">${value}</text>
        <text class="node-lbl" y="42">${label}${extra}</text>
      </g>`;

    const edge = (d: string, active: boolean, reverse: boolean, mag: number) => {
      const dur = active ? Math.max(0.6, 3 - Math.min(mag, 9000) / 3000) : 0;
      return svg`
        <path class="edge" d="${d}"></path>
        <path
          class="edge-flow ${active ? "active" : ""} ${reverse ? "rev" : ""}"
          d="${d}"
          style="${active ? `animation-duration:${dur}s` : ""}"
        ></path>`;
    };

    return html`<div class="flow">
      <svg viewBox="0 0 320 336" preserveAspectRatio="xMidYMid meet">
        ${edge("M160,66 L160,134", pv > TH, false, pv)}
        ${edge("M76,160 L134,160", Number.isNaN(grid) ? false : Math.abs(grid) > TH, grid < 0, Math.abs(grid))}
        ${battery !== null
          ? edge("M244,160 L186,160", Math.abs(battery) > TH, battery > 0, Math.abs(battery))
          : nothing}
        ${edge("M160,186 L160,244", car > TH, false, car)}

        ${node(160, 40, "mdi:solar-power", this._t("flow.solar"), fmtPower(pv))}
        ${node(40, 160, "mdi:transmission-tower", grid < 0 ? this._t("flow.export") : this._t("flow.grid"), fmtPower(Math.abs(grid)))}
        ${battery !== null
          ? node(280, 160, "mdi:home-battery", this._t("flow.battery"), fmtPower(Math.abs(battery)), soc != null ? ` ${Math.round(Number(soc))}%` : "")
          : nothing}
        ${node(160, 160, "mdi:home", this._t("flow.home"), fmtPower(house))}
        ${node(160, 280, connected === false ? "mdi:car-off" : "mdi:car-electric", connected === false ? this._t("flow.no_car") : this._t("flow.car"), fmtPower(car))}
      </svg>
    </div>`;
  }

  // --- Live telemetry ----------------------------------------------------------
  /**
   * A compact stat strip shown while the brain is actively controlling: the
   * target current it's driving the charger at, plus the solar surplus it has to
   * work with in the PV-aware modes. Both come from goe_steve sensors that the
   * card otherwise never surfaces; the flow diagram already shows actual power.
   */
  private _renderLive(ent: ResolvedEntities): TemplateResult | typeof nothing {
    if (!this._isOn(ent.controlling)) return nothing;
    const targetCurrent = this._stateObj(ent.target_current);
    const surplus = this._stateObj(ent.surplus);
    const mode = this._stateObj(ent.charging_mode)?.state ?? "";
    const showSurplus =
      !!surplus &&
      ["pv_only", "pv_minimum", "pv_price", "combined"].includes(mode);
    const validTarget =
      !!targetCurrent &&
      !["unknown", "unavailable", ""].includes(targetCurrent.state);
    if (!validTarget && !showSurplus) return nothing;
    return html`<div class="live">
      ${validTarget
        ? this._stat(this._t("live.target"), this._fmtState(targetCurrent!))
        : nothing}
      ${showSurplus
        ? this._stat(this._t("live.surplus"), this._fmtState(surplus!))
        : nothing}
    </div>`;
  }

  private _stat(label: string, value: string): TemplateResult {
    return html`<div class="stat">
      <span class="stat-label">${label}</span>
      <span class="stat-val">${value}</span>
    </div>`;
  }

  // --- Inline controls ---------------------------------------------------------
  private _renderControls(ent: ResolvedEntities): TemplateResult {
    const mode = this._stateObj(ent.charging_mode);
    const policy = this._stateObj(ent.battery_policy);
    const smart = this._stateObj(ent.smart_control);

    // Battery-level inputs are shown only where they affect the active policy:
    // reserve under Protect and Share, floor under Assist, target energy under
    // the deadline-aware price modes. The reserve/floor each gate whether the
    // battery-hold switch engages during grid charging (Share holds ≤ reserve,
    // Assist holds ≤ floor), so each is surfaced wherever it's in play.
    const reserve = this._stateObj(ent.battery_reserve_soc);
    const floor = this._stateObj(ent.battery_floor_soc);
    const target = this._stateObj(ent.target_energy);
    const policyState = policy?.state;
    const modeState = mode?.state;

    // Manual mode (charging-mode "off") turns the card into the cockpit: the user
    // sets start/stop, current and phases here directly — no go-e app needed. The
    // battery policy below still applies, so it's surfaced in both modes.
    const isManual = modeState === "off";
    const manualCharge = this._stateObj(ent.manual_charge);
    const manualCurrent = this._stateObj(ent.manual_current);
    const manualPhases = this._stateObj(ent.manual_phases);

    // Deadline picker pairs with target energy in the deadline-aware modes; the
    // remaining tunables surface only in the mode where they actually bite.
    const departure = this._stateObj(ent.departure);
    const maxCurrent = this._stateObj(ent.max_current);
    const minGridFloor = this._stateObj(ent.min_grid_floor);

    return html`<div class="controls">
      ${mode
        ? html`<div class="control">
            <span class="ctl-label">${this._t("control.mode")}</span>
            ${this._renderSelect(mode)}
          </div>`
        : nothing}
      ${isManual && manualCharge
        ? html`<div class="control">
            <span class="ctl-label">${this._t("control.manual_charge")}</span>
            <ha-switch
              .checked=${this._isOn(ent.manual_charge)}
              @change=${(e: Event) => this._toggle(ent.manual_charge, e)}
            ></ha-switch>
          </div>`
        : nothing}
      ${isManual && manualCurrent
        ? html`<div class="control">
            <span class="ctl-label">${this._t("control.manual_current")}</span>
            ${this._renderNumber(manualCurrent)}
          </div>`
        : nothing}
      ${isManual && manualPhases
        ? html`<div class="control">
            <span class="ctl-label">${this._t("control.manual_phases")}</span>
            ${this._renderSelect(manualPhases)}
          </div>`
        : nothing}
      ${policy
        ? html`<div class="control">
            <span class="ctl-label">${this._t("control.battery")}</span>
            ${this._renderSelect(policy)}
          </div>`
        : nothing}
      ${reserve && policyState === "protect"
        ? html`<div class="control">
            <span class="ctl-label">${this._t("control.battery_fill_to")}</span>
            ${this._renderNumber(reserve)}
          </div>`
        : nothing}
      ${reserve && policyState === "share"
        ? html`<div class="control">
            <span class="ctl-label">${this._t("control.battery_use_to")}</span>
            ${this._renderNumber(reserve)}
          </div>`
        : nothing}
      ${floor && policyState === "assist"
        ? html`<div class="control">
            <span class="ctl-label">${this._t("control.battery_use_to")}</span>
            ${this._renderNumber(floor)}
          </div>`
        : nothing}
      ${target && (modeState === "price" || modeState === "combined")
        ? html`<div class="control">
            <span class="ctl-label">${this._t("control.target_energy")}</span>
            ${this._renderNumber(target)}
          </div>`
        : nothing}
      ${departure && (modeState === "price" || modeState === "combined")
        ? html`<div class="control">
            <span class="ctl-label">${this._t("control.departure")}</span>
            ${this._renderDateTime(departure)}
          </div>`
        : nothing}
      ${minGridFloor && modeState === "pv_minimum"
        ? html`<div class="control">
            <span class="ctl-label">${this._t("control.min_grid_floor")}</span>
            ${this._renderNumber(minGridFloor)}
          </div>`
        : nothing}
      ${maxCurrent && modeState === "fast"
        ? html`<div class="control">
            <span class="ctl-label">${this._t("control.max_current")}</span>
            ${this._renderNumber(maxCurrent)}
          </div>`
        : nothing}
      ${smart
        ? html`<div class="control">
            <span class="ctl-label">${this._t("control.smart_control")}</span>
            <ha-switch
              .checked=${this._isOn(ent.smart_control)}
              @change=${(e: Event) => this._toggle(ent.smart_control, e)}
            ></ha-switch>
          </div>`
        : nothing}
      ${ent.auto_phase && !isManual
        ? html`<div class="control">
            <span class="ctl-label">${this._t("control.auto_phase")}</span>
            <ha-switch
              .checked=${this._isOn(ent.auto_phase)}
              @change=${(e: Event) => this._toggle(ent.auto_phase, e)}
            ></ha-switch>
          </div>`
        : nothing}
    </div>`;
  }

  /** Native number input bound to a `number` entity (min/max/step from attrs). */
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
        @change=${(e: Event) =>
          this._setNumber(stateObj, (e.target as HTMLInputElement).value)}
      />
      ${unit ? html`<span class="ctl-unit">${unit}</span>` : nothing}
    </span>`;
  }

  private _setNumber(stateObj: HassEntity, value: string): void {
    const num = Number(value);
    if (Number.isNaN(num) || String(num) === stateObj.state) return;
    this.hass.callService("number", "set_value", {
      entity_id: stateObj.entity_id,
      value: num,
    });
  }

  /** Native datetime-local input bound to a `datetime` entity (UTC ISO state). */
  private _renderDateTime(stateObj: HassEntity): TemplateResult {
    return html`<input
      class="ctl-datetime"
      type="datetime-local"
      .value=${this._toLocalInput(stateObj.state)}
      @change=${(e: Event) =>
        this._setDateTime(stateObj, (e.target as HTMLInputElement).value)}
    />`;
  }

  /** UTC ISO → the `YYYY-MM-DDTHH:mm` local string a datetime-local expects. */
  private _toLocalInput(iso: string): string {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return "";
    const pad = (n: number) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
  }

  private _setDateTime(stateObj: HassEntity, value: string): void {
    if (!value) return;
    const d = new Date(value); // parsed in the browser's local zone
    if (Number.isNaN(d.getTime())) return;
    this.hass.callService("datetime", "set_value", {
      entity_id: stateObj.entity_id,
      datetime: d.toISOString(),
    });
  }

  private _renderSelect(stateObj: HassEntity): TemplateResult {
    const options: string[] = stateObj.attributes.options ?? [];
    // A native <select> rather than HA's ha-select (mwc-select): the latter is
    // lazy-loaded, its popup menu is clipped by ha-card's `overflow: hidden`,
    // and its selected-text sync is unreliable inside a card — all of which made
    // the dropdown effectively unusable. The native control always opens (in the
    // browser's own layer, so it can't be clipped) and its change always fires.
    return html`<select
      class="ctl-select"
      @change=${(e: Event) =>
        this._selectOption(stateObj, (e.target as HTMLSelectElement).value)}
    >
      ${options.map(
        (opt) =>
          html`<option .value=${opt} ?selected=${opt === stateObj.state}>
            ${this._localizeOption(stateObj, opt)}
          </option>`,
      )}
    </select>`;
  }

  // --- Charging sessions / per-RFID energy -------------------------------------
  private _renderSessions(ent: ResolvedEntities): TemplateResult | typeof nothing {
    const active = this._stateObj(ent.active_transaction);
    const picker = this._stateObj(ent.selected_tag);

    if (!active && !picker) return nothing;

    // A session is "authorized/running" when SteVe reports an active transaction.
    // The picker's action zone keys off this: authorize/start when idle, stop when
    // charging — the two are mutually exclusive so the same buttons morph.
    const hasActive =
      !!active &&
      !["idle", "unknown", "unavailable", ""].includes(active.state);

    // Live readout for the running session. SteVe has no live meter value, so we
    // pair the session's elapsed time with the actual car power from flow, plus
    // the energy charged so far from the go-e session-energy entity (when mapped).
    const flow = this._stateObj(ent.power_flow)?.attributes;
    const carW = Number(flow?.car_w ?? NaN);
    const energyKwh = Number(flow?.session_energy_kwh ?? NaN);
    const meta = hasActive ? this._sessionMeta(active!, carW, energyKwh) : "";

    return html`<div class="sessions">
      ${this._renderTagPicker(picker, hasActive)}
      ${active
        ? html`<div class="session-row">
            <ha-icon icon="mdi:card-account-details"></ha-icon>
            <span
              >${active.state === "idle"
                ? this._t("session.none")
                : this._t("session.charging", {
                    state: (active.attributes.name as string) ?? active.state,
                  })}${meta ? html`<span class="session-meta"> · ${meta}</span>` : nothing}</span
            >
          </div>`
        : nothing}
    </div>`;
  }

  /**
   * Tag picker (authorized SteVe tags) + a state-driven action zone.
   *
   * While a session is running there is nothing to start: the tag dropdown is
   * hidden (Stop ignores it anyway) and the zone collapses to a single Stop
   * button that ends the active transaction. Back to idle the dropdown returns
   * and offers Start on the picked tag. The Start button acts on the "Selected
   * tag" select (the service defaults id_tag to it), so no UID is typed, and
   * Stop targets the lone active transaction (remote_stop's default).
   *
   * There is deliberately no Authorize button: the picker only ever lists
   * already-authorized (non-blocked) tags, so authorizing the selection would
   * always be a no-op.
   */
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
        : html`<div class="control">
            <span class="ctl-label">${this._t("control.tag")}</span>
            ${this._renderSelect(picker)}
          </div>`}
      <div class="tag-actions">
        ${hasActive
          ? html`<button
              class="tag-btn stop"
              @click=${() => this._confirmStop()}
            >
              <ha-icon icon="mdi:stop"></ha-icon>${this._t("action.stop")}
            </button>`
          : html`<button
                class="tag-btn"
                ?disabled=${!hasSelection}
                @click=${() => this._callTagService("remote_start")}
              >
                <ha-icon icon="mdi:play"></ha-icon>${this._t("action.start")}
              </button>`}
      </div>
    </div>`;
  }

  /** Call a SteVe tag service with no id_tag — it falls back to the selection. */
  private _callTagService(service: string): void {
    this.hass.callService(PLATFORM, service, {});
  }

  /** Stopping ends a live charging session, so confirm before doing it. */
  private _confirmStop(): void {
    if (window.confirm(this._t("action.stop_confirm"))) {
      this._callTagService("remote_stop");
    }
  }

  /**
   * "1h 23m · 8.3 kW · 11.4 kWh" for a running session — elapsed time, live car
   * power, and the energy charged so far (when the go-e session-energy entity is
   * mapped; omitted otherwise).
   */
  private _sessionMeta(active: HassEntity, carW: number, energyKwh: number): string {
    const parts: string[] = [];
    const dur = this._fmtDuration(active.attributes.started as string | undefined);
    if (dur) parts.push(dur);
    if (!Number.isNaN(carW) && carW > 50) parts.push(fmtPower(carW));
    if (!Number.isNaN(energyKwh) && energyKwh > 0)
      parts.push(`${energyKwh.toFixed(2)} kWh`);
    return parts.join(" · ");
  }

  /** Elapsed time since an ISO timestamp as a compact "1h 23m" / "5m" string. */
  private _fmtDuration(started: string | undefined): string {
    if (!started) return "";
    const start = new Date(started).getTime();
    if (Number.isNaN(start)) return "";
    const mins = Math.max(0, Math.round((Date.now() - start) / 60000));
    const h = Math.floor(mins / 60);
    const m = mins % 60;
    return h > 0 ? `${h}h ${m}m` : `${m}m`;
  }

  // --- hass helpers ------------------------------------------------------------
  private _stateObj(id?: string): HassEntity | undefined {
    return id ? this.hass.states[id] : undefined;
  }
  private _isOn(id?: string): boolean {
    return this._stateObj(id)?.state === "on";
  }
  private _displayState(id?: string): string | null {
    const s = this._stateObj(id);
    return s ? this._fmtState(s) : null;
  }
  private _fmtState(s: HassEntity): string {
    return this.hass.formatEntityState ? this.hass.formatEntityState(s) : s.state;
  }
  /**
   * Localize a select option in the user's language via HA's own
   * `formatEntityState`, which reads the integration's entity-state
   * translations. Falls back to the raw option value.
   */
  private _localizeOption(s: HassEntity, opt: string): string {
    // Primary path: look up the integration's own state translation directly.
    // This is the reliable route — it works regardless of HA version quirks in
    // `formatEntityState` and matches what HA shows elsewhere in the UI.
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
    this.hass.callService("select", "select_option", {
      entity_id: stateObj.entity_id,
      option,
    });
  }
  private _toggle(id: string | undefined, e: Event): void {
    if (!id) return;
    const on = (e.target as HTMLInputElement).checked;
    this.hass.callService("switch", on ? "turn_on" : "turn_off", { entity_id: id });
  }

  static styles = css`
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
    .header {
      padding: 16px 16px 8px;
    }
    .title-row {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .title {
      font-size: 1.25rem;
      font-weight: 500;
    }
    .brain {
      color: var(--disabled-text-color);
      transition: color 0.3s ease;
    }
    .brain.active {
      color: var(--primary-color);
    }
    .reason {
      margin-top: 4px;
      color: var(--secondary-text-color);
      font-size: 0.95rem;
      min-height: 1.2em;
    }
    .chips {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 10px;
    }
    .chip {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 3px 10px;
      border-radius: 14px;
      background: var(--secondary-background-color);
      font-size: 0.8rem;
      color: var(--primary-text-color);
    }
    .chip ha-icon {
      --mdc-icon-size: 15px;
      color: var(--primary-color);
    }
    .content {
      padding: 0 8px 8px;
    }

    /* Flow diagram */
    .flow svg {
      width: 100%;
      height: auto;
      max-height: 336px;
    }
    .node circle {
      fill: var(--card-background-color);
      stroke: var(--divider-color);
      stroke-width: 1.5;
    }
    .node ha-icon {
      --mdc-icon-size: 22px;
      color: var(--primary-color);
    }
    .node-val {
      text-anchor: middle;
      font-size: 11px;
      font-weight: 600;
      fill: var(--primary-text-color);
    }
    .node-lbl {
      text-anchor: middle;
      font-size: 10px;
      fill: var(--secondary-text-color);
    }
    .edge {
      fill: none;
      stroke: var(--divider-color);
      stroke-width: 2;
    }
    .edge-flow {
      fill: none;
      stroke: var(--primary-color);
      stroke-width: 3;
      stroke-linecap: round;
      stroke-dasharray: 4 10;
      opacity: 0;
    }
    .edge-flow.active {
      opacity: 0.9;
      animation-name: dash;
      animation-timing-function: linear;
      animation-iteration-count: infinite;
    }
    .edge-flow.active.rev {
      animation-name: dash-rev;
    }
    @keyframes dash {
      to {
        stroke-dashoffset: -14;
      }
    }
    @keyframes dash-rev {
      to {
        stroke-dashoffset: 14;
      }
    }

    /* Controls */
    .controls {
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding: 4px 8px 8px;
    }
    .control {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .ctl-label {
      color: var(--secondary-text-color);
      font-size: 0.9rem;
      white-space: nowrap;
    }
    .ctl-select {
      min-width: 180px;
      flex: 1;
      max-width: 60%;
      padding: 8px 10px;
      border-radius: 8px;
      border: 1px solid var(--divider-color);
      background: var(--card-background-color, var(--ha-card-background));
      color: var(--primary-text-color);
      font-family: inherit;
      font-size: 0.95rem;
      cursor: pointer;
    }
    .ctl-select:focus {
      outline: none;
      border-color: var(--primary-color);
    }
    .ctl-number-wrap {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      flex: 1;
      max-width: 60%;
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
      font-size: 0.95rem;
      text-align: right;
    }
    .ctl-number:focus {
      outline: none;
      border-color: var(--primary-color);
    }
    .ctl-unit {
      color: var(--secondary-text-color);
      font-size: 0.85rem;
      white-space: nowrap;
    }
    .ctl-datetime {
      flex: 1;
      max-width: 60%;
      padding: 8px 10px;
      border-radius: 8px;
      border: 1px solid var(--divider-color);
      background: var(--card-background-color, var(--ha-card-background));
      color: var(--primary-text-color);
      font-family: inherit;
      font-size: 0.95rem;
    }
    .ctl-datetime:focus {
      outline: none;
      border-color: var(--primary-color);
    }

    /* Live telemetry strip */
    .live {
      display: flex;
      gap: 8px;
      padding: 0 8px 8px;
    }
    .stat {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 2px;
      padding: 8px 10px;
      border-radius: 8px;
      background: var(--secondary-background-color);
    }
    .stat-label {
      font-size: 0.75rem;
      color: var(--secondary-text-color);
    }
    .stat-val {
      font-size: 1.05rem;
      font-weight: 600;
      color: var(--primary-text-color);
    }

    /* Sessions */
    .sessions {
      border-top: 1px solid var(--divider-color);
      margin: 4px 8px 0;
      padding-top: 8px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .session-row {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.9rem;
      color: var(--primary-text-color);
    }
    .session-row ha-icon {
      --mdc-icon-size: 18px;
      color: var(--secondary-text-color);
    }
    .session-meta {
      color: var(--secondary-text-color);
    }
    .history {
      display: flex;
      flex-direction: column;
      gap: 2px;
      margin: 2px 0 0 26px;
    }
    .hist-row {
      display: flex;
      justify-content: space-between;
      gap: 8px;
      font-size: 0.82rem;
      color: var(--secondary-text-color);
    }
    .hist-name {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .hist-meta {
      display: inline-flex;
      gap: 6px;
      white-space: nowrap;
    }
    .hist-date {
      opacity: 0.7;
    }
    .tags {
      display: flex;
      flex-direction: column;
      gap: 4px;
      margin-top: 2px;
    }
    .tag {
      display: flex;
      justify-content: space-between;
      font-size: 0.85rem;
      padding: 2px 0;
    }
    .tag-picker {
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding-bottom: 4px;
    }
    .tag-actions {
      display: flex;
      gap: 8px;
    }
    .tag-btn {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      flex: 1;
      justify-content: center;
      padding: 8px 10px;
      border-radius: 8px;
      border: 1px solid var(--divider-color);
      background: var(--card-background-color, var(--ha-card-background));
      color: var(--primary-text-color);
      font-family: inherit;
      font-size: 0.9rem;
      cursor: pointer;
    }
    .tag-btn ha-icon {
      --mdc-icon-size: 18px;
      color: var(--primary-color);
    }
    .tag-btn:hover:not([disabled]) {
      border-color: var(--primary-color);
    }
    .tag-btn[disabled] {
      opacity: 0.5;
      cursor: default;
    }
    .tag-btn.stop {
      color: var(--error-color, #db4437);
    }
    .tag-btn.stop ha-icon {
      color: var(--error-color, #db4437);
    }
    .tag-btn.stop:hover:not([disabled]) {
      border-color: var(--error-color, #db4437);
    }
    .tag-id {
      color: var(--secondary-text-color);
    }
    .tag-kwh {
      font-weight: 600;
    }
    .tag-kwh.blocked {
      color: var(--error-color, #db4437);
      font-weight: 500;
    }
  `;
}

// Register in the card picker.
(window as any).customCards = (window as any).customCards || [];
(window as any).customCards.push({
  type: "goe-steve-card",
  name: "go-e + SteVe Smart Charging",
  description:
    "Live energy flow, charging mode & battery policy with the brain's reasoning, inline controls and per-RFID energy.",
  preview: true,
  documentationURL: "https://github.com/JustChr/HAgoe_steve",
});
