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
  "control.auto_phase": "Auto phase (1↔3)",
  "control.battery_fill_to": "Fill battery to",
  "control.battery_use_to": "Use battery down to",
  "control.target_energy": "Car target energy",
  "control.tag": "Tag",

  "action.start": "Start",
  "action.stop": "Stop",

  "reason.smart_disabled": "Smart control disabled",
  "reason.mode_off": "Mode: Off — manual control",
  "reason.no_car": "No car connected",
  "reason.fast": "Fast charging at {amps} A",
  "reason.cheap_grid": "Cheap grid {price}/kWh ≤ {threshold} → full power",
  "reason.cheap_grid_guarded":
    "Cheap grid {price}/kWh ≤ {threshold} → full power (protecting home battery → {amps} A)",
  "reason.deadline_plan":
    "Cheap-hours plan: charging now at {price}/kWh to reach {target} kWh by departure",
  "reason.deadline_plan_guarded":
    "Cheap-hours plan: charging now at {price}/kWh to reach {target} kWh by departure (protecting home battery → {amps} A)",
  "reason.holding_off_dwell": "Holding off (anti-flap dwell)",
  "reason.price_waiting": "Waiting for a cheaper price window",
  "reason.charging": "Charging",
  "reason.waiting_battery_reserve":
    "Waiting — home battery {soc}% < reserve {reserve}%",
  "reason.waiting_surplus": "Waiting for surplus — {surplus} W < {needed} W needed",
  "reason.solar_surplus": "Solar surplus {surplus} W → {amps} A",
  "reason.solar_surplus_phase": "Solar surplus {surplus} W → {amps} A ({phases}-phase)",
  "reason.solar_min_topup":
    "Minimum {amps} A (surplus only {surplus} W, topping up from grid)",
  "reason.holding_charge_dwell": "Holding charge (anti-flap dwell)",

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
  "editor.hours": "Hours to show (optional)",

  "price.title": "Electricity price",
  "price.no_price":
    "No price forecast available. Configure a price sensor for {name} first.",
  "price.cheap_threshold": "Cheap below",
  "price.cheap_hours": "{hours} cheap upcoming",
  "price.next_window": "next {start}–{end}",
  "price.no_cheap": "No cheap hours coming up at this threshold",
  "price.now": "now",
  "price.tomorrow": "Tomorrow",
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
  "control.auto_phase": "Auto-Phase (1↔3)",
  "control.battery_fill_to": "Batterie laden bis",
  "control.battery_use_to": "Batterie nutzen bis",
  "control.target_energy": "Ziel-Energie Auto",
  "control.tag": "Tag",

  "action.start": "Starten",
  "action.stop": "Stoppen",

  "reason.smart_disabled": "Intelligente Steuerung deaktiviert",
  "reason.mode_off": "Modus: Aus — manuelle Steuerung",
  "reason.no_car": "Kein Auto verbunden",
  "reason.fast": "Schnellladen mit {amps} A",
  "reason.cheap_grid": "Günstiger Netzstrom {price}/kWh ≤ {threshold} → volle Leistung",
  "reason.cheap_grid_guarded":
    "Günstiger Netzstrom {price}/kWh ≤ {threshold} → volle Leistung (Hausbatterie geschützt → {amps} A)",
  "reason.deadline_plan":
    "Günstig-Stunden-Plan: lädt jetzt zu {price}/kWh, um {target} kWh bis zur Abfahrt zu erreichen",
  "reason.deadline_plan_guarded":
    "Günstig-Stunden-Plan: lädt jetzt zu {price}/kWh, um {target} kWh bis zur Abfahrt zu erreichen (Hausbatterie geschützt → {amps} A)",
  "reason.holding_off_dwell": "Pausiert (Anti-Flatter-Sperre)",
  "reason.price_waiting": "Warten auf ein günstigeres Preisfenster",
  "reason.charging": "Lädt",
  "reason.waiting_battery_reserve":
    "Warten — Hausbatterie {soc}% < Reserve {reserve}%",
  "reason.waiting_surplus": "Warten auf Überschuss — {surplus} W < {needed} W benötigt",
  "reason.solar_surplus": "Solarüberschuss {surplus} W → {amps} A",
  "reason.solar_surplus_phase": "Solarüberschuss {surplus} W → {amps} A ({phases}-phasig)",
  "reason.solar_min_topup":
    "Minimum {amps} A (nur {surplus} W Überschuss, Aufstockung aus dem Netz)",
  "reason.holding_charge_dwell": "Ladung gehalten (Anti-Flatter-Sperre)",

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
  "editor.hours": "Anzuzeigende Stunden (optional)",

  "price.title": "Strompreis",
  "price.no_price":
    "Keine Preisprognose verfügbar. Richte zuerst einen Preissensor für {name} ein.",
  "price.cheap_threshold": "Günstig unter",
  "price.cheap_hours": "{hours} günstig in Kürze",
  "price.next_window": "nächste {start}–{end}",
  "price.no_cheap": "Bei dieser Schwelle keine günstigen Stunden in Sicht",
  "price.now": "jetzt",
  "price.tomorrow": "Morgen",
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
