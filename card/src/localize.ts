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
  "hero.paused_ready": "Paused · ready on {phases}-phase",
  "hero.asked_takes": "asked {asked} A, car takes {takes} A",
  "hero.solar_share": "{pct} % solar",
  "hero.phase_count": "{phases}-phase",

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
  "balance.reserve": "reserve {pct}%",

  "chip.hold": "Battery discharge blocked",
  "chip.hold_manual": "Discharge blocked (manual)",
  "chip.price_cheap": "{price} {unit} — cheap ✓",
  "chip.price_wait": "{price} {unit} — waiting for ≤ {target}",
  "chip.resume_in": "Can resume in {time}",
  "chip.start_now": "Start now",
  "chip.riding_out": "Riding out dip · {time}",
  "chip.phases": "{phases} φ",
  "chip.forced_off": "Charger forced off",

  "plan.on_track": "on track",
  "plan.tight": "tight — few cheap hours",

  "control.home_battery": "Home battery",
  "control.smart_active": "Smart control is active",
  "control.smart_inactive": "Smart control is off",
  "control.mode": "Mode",

  "mode_hint.manual": "You set current and phases — the charger holds them.",
  "mode_hint.solar": "Charges only from solar surplus.",
  "mode_hint.solar_min":
    "Uses solar surplus, topping up to a minimum rate from the home battery or the grid.",
  "mode_hint.smart":
    "Targets the cheapest hours to reach your goal by departure.",
  "mode_hint.fast": "Charges at full power right now.",
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
  "reason.deadline_urgent_peak":
    "Charging at full power to make the departure target — {remaining} kWh to go, so this quarter-hour will go over your peak limit",
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
  "reason.solar_surplus_battery_topup":
    "Solar surplus {surplus} W → {amps} A — the last {gap} W come from the home battery instead of being exported",
  "reason.solar_min_covered": "Minimum {amps} A — the {surplus} W surplus covers it",
  "reason.solar_min_topup":
    "Minimum {amps} A — surplus is only {surplus} W, so the last {gap} W come from the grid",
  "reason.solar_min_topup_battery":
    "Minimum {amps} A — surplus is only {surplus} W, so the last {gap} W come from the home battery",

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
  "editor.demand_rate": "Demand charge per kW of monthly peak (optional)",
  "editor.currency": "Currency symbol",
  "editor.show_settings": "Show the settings block",

  "chip.peak_soft": "Easing off — {projected} kW this ¼ h",
  "chip.peak_hard": "Peak limit — {projected} kW this ¼ h",
  "chip.peak_degraded": "Peak reading incomplete",
  "chip.grid_charging": "Buying cheap — {power} W",

  "peak.title": "Peak protection",
  "peak.month_label": "Highest ¼ hour this month",
  "peak.month_at": "on {when}",
  "peak.month_none": "Nothing recorded yet this month",
  "peak.month_cost": "≈ {cost} at {rate}/kW",
  "peak.record_risk": "This quarter-hour is on track to beat it",
  "peak.window_label": "This quarter-hour",
  "peak.heading_for": "heading for {projected} kW",
  "peak.time_left": "{time} left",
  "peak.soft": "ease off",
  "peak.target": "target",
  "peak.hard": "hard",
  "peak.allowance": "Limit raised to {value} kW — this month already cost {month} kW",
  "peak.degraded": "Part of this quarter-hour went unmeasured — holding the limit",
  "peak.off": "Measuring only. Turn on Peak protection to let it act.",
  "peak.recent": "Recent quarter-hours",
  "peak.recent_none": "No completed quarter-hours yet.",
  "peak.forecast": "Cheap hours ahead",
  "peak.forecast_none": "No price forecast available.",
  "peak.buying_to": "Buying to {target} %",
  "peak.bright": "bright tomorrow",
  "peak.dark": "little sun tomorrow",
  "peak.settings": "Settings",
  "peak.limits": "Limits",
  "peak.battery": "Home battery",
  "peak.cheap": "Cheap hours",
  "peak.stockUp": "Stocking up",

  "reason.peak_off": "Peak protection is off",
  "reason.peak_ok": "This quarter-hour is heading for {projected} kW — comfortable",
  "reason.peak_watch":
    "This quarter-hour is heading for {projected} kW, close to the {soft} kW easing-off point",
  "reason.peak_holding": "Holding this quarter-hour under {target} kW — at {projected} kW",
  "reason.peak_shaving_car":
    "Heading for {projected} kW — easing the car back to {amps} A to stay under {target} kW",
  "reason.peak_shaving_house":
    "Heading for {projected} kW — letting the home battery cover more of the house to stay under {target} kW",
  "reason.peak_pause":
    "Heading for {projected} kW — the car is paused until this quarter-hour is over at {until}",
  "reason.peak_battery_empty":
    "Heading for {projected} kW and the home battery is down to its {soc}% floor — nothing left to shave with",
  "reason.peak_degraded":
    "The grid reading was missing for part of this quarter-hour — holding the current limit until {until} to be safe",
  "reason.peak_month_headroom":
    "This month already peaked at {month} kW, so there is nothing to save by holding below it — aiming at {target} kW, just under the record",
  "reason.grid_charge_dark":
    "Cheap hour at {price}/kWh and little sun expected — importing {power} W to fill the home battery to {target}%",
  "reason.grid_charge_bright":
    "Cheap hour at {price}/kWh, but tomorrow looks bright — filling the home battery only to {target}% so the sun has somewhere to go",
  "reason.grid_charge_full": "Home battery at {soc}% — nothing left to buy this cheaply",
  "reason.grid_charge_ready":
    "Home battery down to {soc}% and too low to hold the peak limit — importing {power} W to get it back to {target}%, cheap hour or not",
  "reason.grid_charge_stock_up":
    "Stocking up for tonight — importing {power} W to fill the home battery to {target}% and holding it there",
  "reason.grid_charge_stocked":
    "Stocked up: home battery at {soc}%, holding it for tonight",

  "price.title": "Electricity price",
  "price.avg": "avg",
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
  "hero.paused_ready": "Pausiert · bereit auf {phases}-phasig",
  "hero.asked_takes": "angefordert {asked} A, Auto nimmt {takes} A",
  "hero.solar_share": "{pct} % Solar",
  "hero.phase_count": "{phases}-phasig",

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
  "balance.reserve": "Reserve {pct}%",

  "chip.hold": "Batterieentladung gesperrt",
  "chip.hold_manual": "Entladung gesperrt (manuell)",
  "chip.price_cheap": "{price} {unit} — günstig ✓",
  "chip.price_wait": "{price} {unit} — warten auf ≤ {target}",
  "chip.resume_in": "Fortsetzen in {time}",
  "chip.start_now": "Jetzt starten",
  "chip.riding_out": "Überbrücke Einbruch · {time}",
  "chip.phases": "{phases} φ",
  "chip.forced_off": "Wallbox zwangsweise aus",

  "plan.on_track": "im Plan",
  "plan.tight": "knapp — wenige günstige Stunden",

  "control.home_battery": "Hausbatterie",
  "control.smart_active": "Intelligente Steuerung aktiv",
  "control.smart_inactive": "Intelligente Steuerung aus",
  "control.mode": "Modus",

  "mode_hint.manual": "Du gibst Strom und Phasen vor — die Wallbox hält sie.",
  "mode_hint.solar": "Lädt nur aus Solarüberschuss.",
  "mode_hint.solar_min":
    "Nutzt Solarüberschuss und stockt bis zu einer Mindestrate aus Hausbatterie oder Netz auf.",
  "mode_hint.smart":
    "Steuert die günstigsten Stunden an, um dein Ziel bis zur Abfahrt zu erreichen.",
  "mode_hint.fast": "Lädt jetzt mit voller Leistung.",
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
  "reason.deadline_urgent_peak":
    "Lädt mit voller Leistung für das Abfahrtsziel — noch {remaining} kWh, daher überschreitet diese Viertelstunde die Lastspitzen-Grenze",
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
  "reason.solar_surplus_battery_topup":
    "Solarüberschuss {surplus} W → {amps} A — die letzten {gap} W kommen aus der Hausbatterie statt ins Netz zu gehen",
  "reason.solar_min_covered": "Minimum {amps} A — {surplus} W Überschuss decken das",
  "reason.solar_min_topup":
    "Minimum {amps} A — nur {surplus} W Überschuss, die letzten {gap} W kommen aus dem Netz",
  "reason.solar_min_topup_battery":
    "Minimum {amps} A — nur {surplus} W Überschuss, die letzten {gap} W kommen aus der Hausbatterie",

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
  "editor.demand_rate": "Leistungspreis je kW Monatsspitze (optional)",
  "editor.currency": "Währungssymbol",
  "editor.show_settings": "Einstellungen anzeigen",

  "chip.peak_soft": "Nimmt zurück — {projected} kW diese ¼ h",
  "chip.peak_hard": "Lastspitze — {projected} kW diese ¼ h",
  "chip.peak_degraded": "Messung der Spitze unvollständig",
  "chip.grid_charging": "Kauft günstig — {power} W",

  "peak.title": "Lastspitzenschutz",
  "peak.month_label": "Höchste ¼ Stunde dieses Monats",
  "peak.month_at": "am {when}",
  "peak.month_none": "Diesen Monat noch nichts erfasst",
  "peak.month_cost": "≈ {cost} bei {rate}/kW",
  "peak.record_risk": "Diese Viertelstunde ist auf dem Weg, das zu übertreffen",
  "peak.window_label": "Diese Viertelstunde",
  "peak.heading_for": "läuft auf {projected} kW zu",
  "peak.time_left": "noch {time}",
  "peak.soft": "zurücknehmen",
  "peak.target": "Ziel",
  "peak.hard": "hart",
  "peak.allowance": "Grenze auf {value} kW angehoben — der Monat kostet bereits {month} kW",
  "peak.degraded": "Ein Teil dieser Viertelstunde wurde nicht gemessen — Grenze bleibt",
  "peak.off": "Nur Messung. Schalte den Lastspitzenschutz ein, damit er eingreift.",
  "peak.recent": "Letzte Viertelstunden",
  "peak.recent_none": "Noch keine abgeschlossene Viertelstunde.",
  "peak.forecast": "Günstige Stunden voraus",
  "peak.forecast_none": "Keine Preisprognose verfügbar.",
  "peak.buying_to": "Kauft bis {target} %",
  "peak.bright": "morgen sonnig",
  "peak.dark": "morgen wenig Sonne",
  "peak.settings": "Einstellungen",
  "peak.limits": "Grenzen",
  "peak.battery": "Hausbatterie",
  "peak.cheap": "Günstige Stunden",
  "peak.stockUp": "Vorladen",

  "reason.peak_off": "Lastspitzenschutz ist aus",
  "reason.peak_ok": "Diese Viertelstunde läuft auf {projected} kW zu — entspannt",
  "reason.peak_watch":
    "Diese Viertelstunde läuft auf {projected} kW zu, nahe an der Zurücknehmen-Schwelle von {soft} kW",
  "reason.peak_holding":
    "Hält diese Viertelstunde unter {target} kW — aktuell {projected} kW",
  "reason.peak_shaving_car":
    "Läuft auf {projected} kW zu — nimmt das Auto auf {amps} A zurück, um unter {target} kW zu bleiben",
  "reason.peak_shaving_house":
    "Läuft auf {projected} kW zu — die Hausbatterie übernimmt mehr vom Haus, um unter {target} kW zu bleiben",
  "reason.peak_pause":
    "Läuft auf {projected} kW zu — das Auto pausiert, bis diese Viertelstunde um {until} vorbei ist",
  "reason.peak_battery_empty":
    "Läuft auf {projected} kW zu und die Hausbatterie ist auf ihrer {soc}%-Grenze — nichts mehr zum Kappen da",
  "reason.peak_degraded":
    "Der Netzwert fehlte für einen Teil dieser Viertelstunde — die Grenze bleibt bis {until} bestehen",
  "reason.peak_month_headroom":
    "Dieser Monat hatte bereits {month} kW Spitze — darunter zu bleiben spart nichts mehr; Ziel sind {target} kW, knapp darunter",
  "reason.grid_charge_dark":
    "Günstige Stunde zu {price}/kWh und wenig Sonne erwartet — bezieht {power} W, um die Hausbatterie auf {target}% zu füllen",
  "reason.grid_charge_bright":
    "Günstige Stunde zu {price}/kWh, aber morgen wird es sonnig — füllt die Hausbatterie nur auf {target}%, damit die Sonne noch Platz hat",
  "reason.grid_charge_full":
    "Hausbatterie bei {soc}% — zu diesem Preis gibt es nichts mehr zu kaufen",
  "reason.grid_charge_ready":
    "Hausbatterie nur noch bei {soc}% und zu leer, um die Lastspitze zu halten — bezieht {power} W zurück auf {target}%, günstige Stunde hin oder her",
  "reason.grid_charge_stock_up":
    "Lädt für heute Abend vor — bezieht {power} W, um die Hausbatterie auf {target}% zu füllen und dort zu halten",
  "reason.grid_charge_stocked":
    "Vorgeladen: Hausbatterie bei {soc}%, wird für heute Abend gehalten",

  "price.title": "Strompreis",
  "price.avg": "Mittel",
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
