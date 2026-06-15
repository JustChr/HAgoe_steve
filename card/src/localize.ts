/** Tiny i18n layer for the card's own chrome (labels HA doesn't translate for us). */

interface HassLike {
  language?: string;
  locale?: { language?: string };
}

type Dict = Record<string, string>;

const en: Dict = {
  "card.no_device":
    "No {name} device found. Set one up first, then add this card.",
  "card.default_title": "Smart Charging",

  "flow.solar": "Solar",
  "flow.grid": "Grid",
  "flow.export": "Export",
  "flow.battery": "Battery",
  "flow.home": "Home",
  "flow.car": "Car",
  "flow.no_car": "No car",

  "control.mode": "Mode",
  "control.battery": "Battery",
  "control.smart_control": "Smart control",

  "session.none": "No active session",
  "session.charging": "Charging: {state}",
  "session.last": "Last session: {energy}",
  "session.blocked": "blocked",
  "session.tag": "tag",

  "editor.device": "Smart Charging device (optional — auto-detected)",
  "editor.title": "Title (optional)",
  "editor.show_flow": "Show energy flow",
  "editor.show_controls": "Show controls",
  "editor.show_sessions": "Show sessions & RFID",
};

const de: Dict = {
  "card.no_device":
    "Kein {name}-Gerät gefunden. Richte zuerst eines ein und füge dann diese Karte hinzu.",
  "card.default_title": "Intelligentes Laden",

  "flow.solar": "Solar",
  "flow.grid": "Netz",
  "flow.export": "Einspeisung",
  "flow.battery": "Batterie",
  "flow.home": "Haus",
  "flow.car": "Auto",
  "flow.no_car": "Kein Auto",

  "control.mode": "Modus",
  "control.battery": "Batterie",
  "control.smart_control": "Intelligente Steuerung",

  "session.none": "Kein aktiver Ladevorgang",
  "session.charging": "Lädt: {state}",
  "session.last": "Letzter Ladevorgang: {energy}",
  "session.blocked": "gesperrt",
  "session.tag": "Tag",

  "editor.device": "Smart-Charging-Gerät (optional — automatisch erkannt)",
  "editor.title": "Titel (optional)",
  "editor.show_flow": "Energiefluss anzeigen",
  "editor.show_controls": "Steuerung anzeigen",
  "editor.show_sessions": "Ladevorgänge & RFID anzeigen",
};

const LANGUAGES: Record<string, Dict> = { en, de };

/** Pick the active dictionary from `hass`, falling back to English. */
function dictFor(hass: HassLike | undefined): Dict {
  const lang = (hass?.locale?.language || hass?.language || "en")
    .toLowerCase()
    .split("-")[0];
  return LANGUAGES[lang] ?? en;
}

/** Translate `key`, substituting `{placeholders}` from `params`. */
export function localize(
  hass: HassLike | undefined,
  key: string,
  params: Record<string, string> = {},
): string {
  const dict = dictFor(hass);
  let str = dict[key] ?? en[key] ?? key;
  for (const [name, value] of Object.entries(params)) {
    str = str.replace(`{${name}}`, value);
  }
  return str;
}
