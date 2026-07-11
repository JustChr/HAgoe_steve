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

  "live.live": "live",
  "live.updated_ago": "updated {ago} ago",

  "hero.not_connected": "Not connected",
  "hero.paused": "Paused",
  "hero.paused_ready": "Paused · ready on {phases} φ",
  "hero.asked_takes": "asked {asked} A, car takes {takes} A",
  "hero.solar_share": "{pct} % solar",

  "source.solar": "Solar",
  "source.battery": "Battery",
  "source.grid": "Grid",
  "source.to_car": "{source} → car: {watts} of {total}",
  "source.none": "Nothing flowing from {source} right now.",
  "source.tap_hint": "Tap a segment for exact watts.",
  "source.exporting": "House running on PV — surplus is exporting.",
  "source.paused": "Car paused — no power flowing.",

  "balance.pv": "PV",
  "balance.house": "House",
  "balance.grid": "Grid",
  "balance.export": "Export",
  "balance.battery": "Battery",
  "balance.idle": "idle",

  "chip.hold": "Battery discharge blocked",
  "chip.hold_manual": "Discharge blocked (manual)",
  "chip.price_cheap": "{price} {unit} — cheap ✓",
  "chip.price_wait": "{price} {unit} — waiting for ≤ {target}",
  "chip.resume_in": "Can resume in {time}",
  "chip.riding_out": "Riding out dip · {time}",
  "chip.phases": "{phases} φ",
  "chip.forced_off": "Charger forced off",

  "plan.on_track": "on track",
  "plan.tight": "tight — few cheap hours",

  "control.home_battery": "Home battery",
  "control.mode": "Mode",
  "control.manual_charge": "Charge now",
  "control.manual_current": "Current",
  "control.manual_phases": "Phases",
  "control.smart_control": "Smart control",
  "control.auto_phase": "Auto phase (1↔3)",
  "control.battery_reserve": "Keep battery above",
  "control.target_energy": "Car target energy",
  "control.departure": "Departure",
  "control.max_current": "Max current",
  "control.min_current": "Min current",
  "control.tag": "Tag",

  "live.target": "Target",
  "live.surplus": "Surplus",

  "action.start": "Start",
  "action.stop": "Stop",
  "action.start_charging": "Start charging",
  "action.stop_charging": "Stop charging",
  "action.stop_confirm": "Stop the active charging session?",

  "session.none_hint": "No active session — plug in and pick a tag to start.",

  "reason.smart_disabled": "Smart control disabled",
  "reason.manual_passive": "Manual mode — charger left as-is",
  "reason.manual_paused": "Manual mode — paused",
  "reason.manual_charging": "Manual charging at {amps} A",
  "reason.manual_charging_guarded":
    "Manual charging at {amps} A (protecting home battery)",
  "reason.no_car": "No car connected",
  "reason.fast": "Fast charging at {amps} A",
  "reason.cheap_grid": "Cheap grid {price}/kWh ≤ {threshold} → full power",
  "reason.cheap_grid_guarded":
    "Cheap grid {price}/kWh ≤ {threshold} → full power (protecting home battery → {amps} A)",
  "reason.deadline_plan":
    "Planned cheap hour at {price}/kWh — {remaining} kWh to go by departure",
  "reason.deadline_plan_guarded":
    "Planned cheap hour at {price}/kWh — {remaining} kWh to go by departure (protecting home battery → {amps} A)",
  "reason.deadline_urgent":
    "Charging now to make the departure target — {remaining} kWh to go",
  "reason.target_reached": "Departure target reached — {delivered} kWh charged",
  "reason.plan_waiting": "Waiting for a planned cheap hour",
  "reason.waiting_battery_reserve":
    "Waiting — home battery {soc}% < reserve {reserve}%",
  "reason.waiting_surplus": "Waiting for surplus — {surplus} W < {needed} W needed",
  "reason.surplus_confirm": "Surplus {surplus} W — confirming before start",
  "reason.surplus_ride_out": "Surplus dipped — riding it out at {amps} A",
  "reason.solar_surplus": "Solar surplus {surplus} W → {amps} A",
  "reason.solar_surplus_phase": "Solar surplus {surplus} W → {amps} A ({phases}-phase)",
  "reason.solar_surplus_eased":
    "Solar surplus {surplus} W → {amps} A (easing off home battery)",
  "reason.solar_min_topup":
    "Minimum {amps} A (surplus only {surplus} W, topping up from grid)",

  "session.none": "No active session",
  "session.charging": "Charging: {state}",
  "session.last": "Last session: {energy}",
  "session.blocked": "blocked",
  "session.tag": "tag",

  "editor.device": "Smart Charging device (optional — auto-detected)",
  "editor.title": "Title (optional)",
  "editor.show_flow": "Show source bar & balance",
  "editor.show_controls": "Show controls",
  "editor.show_sessions": "Show sessions & RFID",
  "editor.compact": "Compact (hide controls — wall dashboards)",
  "editor.hours": "Hours to show (optional)",
  "editor.charge_hours": "Cheapest-window length (0 hides it)",

  "price.title": "Electricity price",
  "price.no_price":
    "No price forecast available. Configure a price sensor for {name} first.",
  "price.cheap_threshold": "Cheap below",
  "price.cheap_hours": "{hours} cheap upcoming",
  "price.next_window": "next {start}–{end}",
  "price.no_cheap": "No cheap hours coming up at this threshold",
  "price.now": "now",
  "price.tomorrow": "Tomorrow",
  "price.cheapest_window": "Cheapest {hours} h",
};

const de: Dict = {
  "card.no_device":
    "Kein {name}-Gerät gefunden. Richte zuerst eines ein und füge dann diese Karte hinzu.",
  "card.default_title": "Intelligentes Laden",

  "live.live": "live",
  "live.updated_ago": "vor {ago} aktualisiert",

  "hero.not_connected": "Nicht verbunden",
  "hero.paused": "Pausiert",
  "hero.paused_ready": "Pausiert · bereit auf {phases} φ",
  "hero.asked_takes": "angefordert {asked} A, Auto nimmt {takes} A",
  "hero.solar_share": "{pct} % Solar",

  "source.solar": "Solar",
  "source.battery": "Batterie",
  "source.grid": "Netz",
  "source.to_car": "{source} → Auto: {watts} von {total}",
  "source.none": "Aus {source} fließt gerade nichts.",
  "source.tap_hint": "Segment antippen für exakte Watt.",
  "source.exporting": "Haus läuft auf PV — Überschuss wird eingespeist.",
  "source.paused": "Auto pausiert — kein Fluss.",

  "balance.pv": "PV",
  "balance.house": "Haus",
  "balance.grid": "Netz",
  "balance.export": "Einspeisung",
  "balance.battery": "Batterie",
  "balance.idle": "inaktiv",

  "chip.hold": "Batterieentladung gesperrt",
  "chip.hold_manual": "Entladung gesperrt (manuell)",
  "chip.price_cheap": "{price} {unit} — günstig ✓",
  "chip.price_wait": "{price} {unit} — warten auf ≤ {target}",
  "chip.resume_in": "Fortsetzen in {time}",
  "chip.riding_out": "Überbrücke Einbruch · {time}",
  "chip.phases": "{phases} φ",
  "chip.forced_off": "Wallbox zwangsweise aus",

  "plan.on_track": "im Plan",
  "plan.tight": "knapp — wenige günstige Stunden",

  "control.home_battery": "Hausbatterie",
  "control.mode": "Modus",
  "control.manual_charge": "Jetzt laden",
  "control.manual_current": "Stromstärke",
  "control.manual_phases": "Phasen",
  "control.smart_control": "Intelligente Steuerung",
  "control.auto_phase": "Auto-Phase (1↔3)",
  "control.battery_reserve": "Batterie halten über",
  "control.target_energy": "Ziel-Energie Auto",
  "control.departure": "Abfahrt",
  "control.max_current": "Max. Strom",
  "control.min_current": "Min. Strom",
  "control.tag": "Tag",

  "live.target": "Ziel",
  "live.surplus": "Überschuss",

  "action.start": "Starten",
  "action.stop": "Stoppen",
  "action.start_charging": "Laden starten",
  "action.stop_charging": "Laden stoppen",
  "action.stop_confirm": "Aktiven Ladevorgang stoppen?",

  "session.none_hint": "Kein aktiver Ladevorgang — einstecken und einen Tag wählen.",

  "reason.smart_disabled": "Intelligente Steuerung deaktiviert",
  "reason.manual_passive": "Manueller Modus — Wallbox unverändert",
  "reason.manual_paused": "Manueller Modus — pausiert",
  "reason.manual_charging": "Manuelles Laden mit {amps} A",
  "reason.manual_charging_guarded":
    "Manuelles Laden mit {amps} A (Hausbatterie geschützt)",
  "reason.no_car": "Kein Auto verbunden",
  "reason.fast": "Schnellladen mit {amps} A",
  "reason.cheap_grid": "Günstiger Netzstrom {price}/kWh ≤ {threshold} → volle Leistung",
  "reason.cheap_grid_guarded":
    "Günstiger Netzstrom {price}/kWh ≤ {threshold} → volle Leistung (Hausbatterie geschützt → {amps} A)",
  "reason.deadline_plan":
    "Geplante Günstig-Stunde zu {price}/kWh — noch {remaining} kWh bis zur Abfahrt",
  "reason.deadline_plan_guarded":
    "Geplante Günstig-Stunde zu {price}/kWh — noch {remaining} kWh bis zur Abfahrt (Hausbatterie geschützt → {amps} A)",
  "reason.deadline_urgent":
    "Lädt jetzt, um das Abfahrtsziel zu erreichen — noch {remaining} kWh",
  "reason.target_reached": "Abfahrtsziel erreicht — {delivered} kWh geladen",
  "reason.plan_waiting": "Warten auf eine geplante Günstig-Stunde",
  "reason.waiting_battery_reserve":
    "Warten — Hausbatterie {soc}% < Reserve {reserve}%",
  "reason.waiting_surplus": "Warten auf Überschuss — {surplus} W < {needed} W benötigt",
  "reason.surplus_confirm": "Überschuss {surplus} W — kurze Bestätigung vor dem Start",
  "reason.surplus_ride_out": "Überschuss eingebrochen — überbrückt mit {amps} A",
  "reason.solar_surplus": "Solarüberschuss {surplus} W → {amps} A",
  "reason.solar_surplus_phase": "Solarüberschuss {surplus} W → {amps} A ({phases}-phasig)",
  "reason.solar_surplus_eased":
    "Solarüberschuss {surplus} W → {amps} A (Hausbatterie wird entlastet)",
  "reason.solar_min_topup":
    "Minimum {amps} A (nur {surplus} W Überschuss, Aufstockung aus dem Netz)",

  "session.none": "Kein aktiver Ladevorgang",
  "session.charging": "Lädt: {state}",
  "session.last": "Letzter Ladevorgang: {energy}",
  "session.blocked": "gesperrt",
  "session.tag": "Tag",

  "editor.device": "Smart-Charging-Gerät (optional — automatisch erkannt)",
  "editor.title": "Titel (optional)",
  "editor.show_flow": "Quellenbalken & Bilanz anzeigen",
  "editor.show_controls": "Steuerung anzeigen",
  "editor.show_sessions": "Ladevorgänge & RFID anzeigen",
  "editor.compact": "Kompakt (Steuerung ausblenden — Wand-Dashboards)",
  "editor.hours": "Anzuzeigende Stunden (optional)",
  "editor.charge_hours": "Länge des Günstig-Fensters (0 blendet es aus)",

  "price.title": "Strompreis",
  "price.no_price":
    "Keine Preisprognose verfügbar. Richte zuerst einen Preissensor für {name} ein.",
  "price.cheap_threshold": "Günstig unter",
  "price.cheap_hours": "{hours} günstig in Kürze",
  "price.next_window": "nächste {start}–{end}",
  "price.no_cheap": "Bei dieser Schwelle keine günstigen Stunden in Sicht",
  "price.now": "jetzt",
  "price.tomorrow": "Morgen",
  "price.cheapest_window": "Günstigste {hours} h",
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
