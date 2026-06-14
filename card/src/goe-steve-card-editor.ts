import { LitElement, html, css, nothing, type TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import { PLATFORM } from "./entities";

interface Hass {
  localize: (key: string) => string;
}

interface GoeSteveCardConfig {
  type: string;
  device?: string;
  title?: string;
  show_flow?: boolean;
  show_controls?: boolean;
  show_sessions?: boolean;
}

/**
 * Visual editor. Uses ha-form with a device selector filtered to this
 * integration, plus toggles for the optional card sections.
 */
@customElement("goe-steve-card-editor")
export class GoeSteveCardEditor extends LitElement {
  @property({ attribute: false }) public hass!: Hass;
  @state() private _config!: GoeSteveCardConfig;

  public setConfig(config: GoeSteveCardConfig): void {
    this._config = config;
  }

  private _schema = [
    {
      name: "device",
      selector: { device: { integration: PLATFORM } },
    },
    { name: "title", selector: { text: {} } },
    {
      type: "grid",
      name: "",
      schema: [
        { name: "show_flow", selector: { boolean: {} } },
        { name: "show_controls", selector: { boolean: {} } },
        { name: "show_sessions", selector: { boolean: {} } },
      ],
    },
  ];

  private _label = (schema: { name: string }): string => {
    switch (schema.name) {
      case "device":
        return "Smart Charging device (optional — auto-detected)";
      case "title":
        return "Title (optional)";
      case "show_flow":
        return "Show energy flow";
      case "show_controls":
        return "Show controls";
      case "show_sessions":
        return "Show sessions & RFID";
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
