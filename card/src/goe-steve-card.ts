import { LitElement, html, css, svg, nothing, type TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import "./goe-steve-card-editor";
import {
  PLATFORM,
  resolveEntities,
  findDevices,
  type ResolvedEntities,
} from "./entities";

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
  callService: (domain: string, service: string, data: Record<string, any>) => Promise<unknown>;
  formatEntityState?: (stateObj: HassEntity) => string;
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

  protected render(): TemplateResult | typeof nothing {
    if (!this.hass || !this._config) return nothing;

    const ent = this._entities;
    if (!ent || !ent.deviceId) {
      return html`<ha-card>
        <div class="empty">
          <ha-icon icon="mdi:ev-station"></ha-icon>
          <p>No <b>go-e + SteVe Smart Charging</b> device found. Set one up first, then add this card.</p>
        </div>
      </ha-card>`;
    }

    const title =
      this._config.title ?? this._deviceName(ent.deviceId) ?? "Smart Charging";

    return html`<ha-card>
      ${this._renderHeader(ent, title)}
      <div class="content">
        ${this._config.show_flow ? this._renderFlow(ent) : nothing}
        ${this._config.show_controls ? this._renderControls(ent) : nothing}
        ${this._config.show_sessions ? this._renderSessions(ent) : nothing}
      </div>
    </ha-card>`;
  }

  // --- Header: status reason + mode/policy chips --------------------------------
  private _renderHeader(ent: ResolvedEntities, title: string): TemplateResult {
    const status = this._stateObj(ent.status);
    const reason = status?.state && status.state !== "unknown" ? status.state : "—";
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
      <svg viewBox="0 0 320 320" preserveAspectRatio="xMidYMid meet">
        ${edge("M160,66 L160,134", pv > TH, false, pv)}
        ${edge("M76,160 L134,160", Number.isNaN(grid) ? false : Math.abs(grid) > TH, grid < 0, Math.abs(grid))}
        ${battery !== null
          ? edge("M244,160 L186,160", Math.abs(battery) > TH, battery > 0, Math.abs(battery))
          : nothing}
        ${edge("M160,186 L160,244", car > TH, false, car)}

        ${node(160, 40, "mdi:solar-power", "Solar", fmtPower(pv))}
        ${node(40, 160, "mdi:transmission-tower", grid < 0 ? "Export" : "Grid", fmtPower(Math.abs(grid)))}
        ${battery !== null
          ? node(280, 160, "mdi:home-battery", "Battery", fmtPower(Math.abs(battery)), soc != null ? ` ${Math.round(Number(soc))}%` : "")
          : nothing}
        ${node(160, 160, "mdi:home", "Home", fmtPower(house))}
        ${node(160, 280, connected === false ? "mdi:car-off" : "mdi:car-electric", connected === false ? "No car" : "Car", fmtPower(car))}
      </svg>
    </div>`;
  }

  // --- Inline controls ---------------------------------------------------------
  private _renderControls(ent: ResolvedEntities): TemplateResult {
    const mode = this._stateObj(ent.charging_mode);
    const policy = this._stateObj(ent.battery_policy);
    const smart = this._stateObj(ent.smart_control);

    return html`<div class="controls">
      ${mode
        ? html`<div class="control">
            <span class="ctl-label">Mode</span>
            ${this._renderSelect(mode)}
          </div>`
        : nothing}
      ${policy
        ? html`<div class="control">
            <span class="ctl-label">Battery</span>
            ${this._renderSelect(policy)}
          </div>`
        : nothing}
      ${smart
        ? html`<div class="control">
            <span class="ctl-label">Smart control</span>
            <ha-switch
              .checked=${this._isOn(ent.smart_control)}
              @change=${(e: Event) => this._toggle(ent.smart_control, e)}
            ></ha-switch>
          </div>`
        : nothing}
    </div>`;
  }

  private _renderSelect(stateObj: HassEntity): TemplateResult {
    const options: string[] = stateObj.attributes.options ?? [];
    return html`<ha-select
      naturalMenuWidth
      .value=${stateObj.state}
      @selected=${(e: any) => this._selectOption(stateObj, e.target.value)}
      @closed=${(e: Event) => e.stopPropagation()}
    >
      ${options.map(
        (opt) =>
          html`<mwc-list-item .value=${opt}>${this._localizeOption(stateObj, opt)}</mwc-list-item>`,
      )}
    </ha-select>`;
  }

  // --- Charging sessions / per-RFID energy -------------------------------------
  private _renderSessions(ent: ResolvedEntities): TemplateResult | typeof nothing {
    const active = this._stateObj(ent.active_transaction);
    const last = this._stateObj(ent.last_session_energy);
    const tags = ent.tag_energy
      .map((id) => this._stateObj(id))
      .filter((s): s is HassEntity => !!s);

    if (!active && !last && tags.length === 0) return nothing;

    return html`<div class="sessions">
      ${active
        ? html`<div class="session-row">
            <ha-icon icon="mdi:card-account-details"></ha-icon>
            <span>${active.state === "idle" ? "No active session" : `Charging: ${active.state}`}</span>
          </div>`
        : nothing}
      ${last && last.state && last.state !== "unknown"
        ? html`<div class="session-row">
            <ha-icon icon="mdi:history"></ha-icon>
            <span>Last session: ${this._fmtState(last)}</span>
          </div>`
        : nothing}
      ${tags.length
        ? html`<div class="tags">
            ${tags.map(
              (t) => html`<div class="tag">
                <span class="tag-id">${t.attributes.id_tag ?? "tag"}</span>
                <span class="tag-kwh ${t.attributes.blocked ? "blocked" : ""}">
                  ${this._fmtState(t)}${t.attributes.blocked ? " · blocked" : ""}
                </span>
              </div>`,
            )}
          </div>`
        : nothing}
    </div>`;
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
  private _localizeOption(s: HassEntity, opt: string): string {
    const reg = this.hass.entities[s.entity_id];
    const key = reg?.translation_key;
    if (key) {
      const tk = this.hass.localize(
        `component.${PLATFORM}.entity.select.${key}.state.${opt}`,
      );
      if (tk) return tk;
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
      max-height: 320px;
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
    ha-select {
      min-width: 180px;
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
