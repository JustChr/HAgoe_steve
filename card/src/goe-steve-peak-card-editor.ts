import { LitElement, html, css, nothing, type TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import { PLATFORM } from "./entities";
import { localize } from "./localize";
import type { GoeStevePeakCardConfig } from "./goe-steve-peak-card";

interface Hass {
  localize: (key: string) => string;
  language?: string;
  locale?: { language?: string };
}

/**
 * Visual editor for the peak card: the device, an optional title, whether to show
 * the settings block, and the demand rate.
 *
 * The rate is a tariff constant the integration has no way to know — it comes off
 * your grid contract, not off any sensor — so it lives here and only ever feeds
 * the "this is costing you X" line.
 */
@customElement("goe-steve-peak-card-editor")
export class GoeStevePeakCardEditor extends LitElement {
  @property({ attribute: false }) public hass!: Hass;
  @state() private _config!: GoeStevePeakCardConfig;

  public setConfig(config: GoeStevePeakCardConfig): void {
    this._config = config;
  }

  private _schema = [
    { name: "device", selector: { device: { integration: PLATFORM } } },
    { name: "title", selector: { text: {} } },
    {
      name: "demand_rate",
      selector: { number: { min: 0, max: 500, step: 0.01, mode: "box" } },
    },
    { name: "currency", selector: { text: {} } },
    { name: "show_settings", selector: { boolean: {} } },
  ];

  private _label = (schema: { name: string }): string => {
    switch (schema.name) {
      case "device":
        return localize(this.hass, "editor.device");
      case "title":
        return localize(this.hass, "editor.title");
      case "demand_rate":
        return localize(this.hass, "editor.demand_rate");
      case "currency":
        return localize(this.hass, "editor.currency");
      case "show_settings":
        return localize(this.hass, "editor.show_settings");
      default:
        return schema.name;
    }
  };

  protected render(): TemplateResult | typeof nothing {
    if (!this.hass || !this._config) return nothing;
    return html`<ha-form
      .hass=${this.hass}
      .data=${this._config}
      .schema=${this._schema}
      .computeLabel=${this._label}
      @value-changed=${this._valueChanged}
    ></ha-form>`;
  }

  private _valueChanged(ev: CustomEvent): void {
    const config = { ...ev.detail.value };
    this.dispatchEvent(
      new CustomEvent("config-changed", { detail: { config }, bubbles: true, composed: true }),
    );
  }

  static styles = css`
    ha-form {
      display: block;
      padding: 8px 0;
    }
  `;
}
