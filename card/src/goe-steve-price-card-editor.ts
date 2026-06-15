import { LitElement, html, css, nothing, type TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import { PLATFORM } from "./entities";
import { localize } from "./localize";
import type { GoeStevePriceCardConfig } from "./goe-steve-price-card";

interface Hass {
  localize: (key: string) => string;
  language?: string;
  locale?: { language?: string };
}

/**
 * Visual editor for the price card: a device selector filtered to this
 * integration, an optional title, and the number of hours to show.
 */
@customElement("goe-steve-price-card-editor")
export class GoeStevePriceCardEditor extends LitElement {
  @property({ attribute: false }) public hass!: Hass;
  @state() private _config!: GoeStevePriceCardConfig;

  public setConfig(config: GoeStevePriceCardConfig): void {
    this._config = config;
  }

  private _schema = [
    { name: "device", selector: { device: { integration: PLATFORM } } },
    { name: "title", selector: { text: {} } },
    { name: "hours", selector: { number: { min: 6, max: 48, mode: "box", unit_of_measurement: "h" } } },
  ];

  private _label = (schema: { name: string }): string => {
    switch (schema.name) {
      case "device":
        return localize(this.hass, "editor.device");
      case "title":
        return localize(this.hass, "editor.title");
      case "hours":
        return localize(this.hass, "editor.hours");
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
