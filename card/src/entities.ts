/** Discovery of the integration's entities from a single config entry / device. */

export const PLATFORM = "goe_steve";

interface RegistryEntry {
  entity_id: string;
  device_id?: string;
  platform?: string;
  translation_key?: string;
}
interface HassLike {
  states: Record<string, { entity_id: string }>;
  entities: Record<string, RegistryEntry>;
  devices: Record<string, { name?: string; name_by_user?: string }>;
}

export interface ResolvedEntities {
  deviceId?: string;
  status?: string;
  power_flow?: string;
  surplus?: string;
  target_current?: string;
  controlling?: string;
  battery_hold?: string;
  charging_mode?: string;
  battery_hold_mode?: string;
  smart_control?: string;
  auto_phase?: string;
  manual_charge?: string;
  start_now?: string;
  manual_current?: string;
  manual_phases?: string;
  battery_reserve_soc?: string;
  target_energy?: string;
  departure?: string;
  max_current?: string;
  min_current?: string;
  price_forecast?: string;
  cheap_price?: string;
  // Peak protection (the capacity tariff). All optional: the peak card degrades to
  // whatever it can find, and the main card hides its strip entirely when absent.
  peak_window_power?: string;
  monthly_peak?: string;
  rolling_grid_power?: string;
  peak_status?: string;
  peak_guard_active?: string;
  peak_guard?: string;
  peak_follow_month?: string;
  grid_charge?: string;
  peak_soft_limit?: string;
  peak_target_limit?: string;
  peak_hard_limit?: string;
  peak_month_buffer?: string;
  shaving_reserve_soc?: string;
  peak_min_soc?: string;
  grid_setpoint?: string;
  cheap_charge_power?: string;
  bright_day_target_soc?: string;
  dark_day_target_soc?: string;
  peak_ready_soc?: string;
  stock_up?: string;
  stock_up_target_soc?: string;
  reset_monthly_peak?: string;
  active_transaction?: string;
  last_session_energy?: string;
  selected_tag?: string;
  tag_energy: string[];
}

/** All distinct devices that own a goe_steve entity, with a friendly name. */
export function findDevices(hass: HassLike): { id: string; name: string }[] {
  const seen = new Map<string, string>();
  for (const entry of Object.values(hass.entities)) {
    if (entry.platform !== PLATFORM || !entry.device_id) continue;
    if (!seen.has(entry.device_id)) {
      const dev = hass.devices[entry.device_id];
      seen.set(entry.device_id, dev?.name_by_user || dev?.name || entry.device_id);
    }
  }
  return [...seen.entries()].map(([id, name]) => ({ id, name }));
}

/**
 * Resolve the well-known entities for one device. When no device is given and
 * exactly one goe_steve device exists, it is used automatically.
 */
export function resolveEntities(hass: HassLike, deviceId?: string): ResolvedEntities {
  const result: ResolvedEntities = { tag_energy: [] };

  if (!deviceId) {
    const devices = findDevices(hass);
    if (devices.length === 1) deviceId = devices[0].id;
  }
  result.deviceId = deviceId;
  if (!deviceId) return result;

  // All registry entries for this device that belong to the integration.
  const entries = Object.values(hass.entities).filter(
    (e) => e.platform === PLATFORM && e.device_id === deviceId,
  );

  const find = (key: string): string | undefined => {
    // Prefer the registry translation_key (stable), fall back to entity_id suffix.
    const byKey = entries.find((e) => e.translation_key === key);
    if (byKey) return byKey.entity_id;
    const bySuffix = entries.find((e) => {
      const obj = e.entity_id.split(".")[1] ?? "";
      return obj === key || obj.endsWith(`_${key}`);
    });
    return bySuffix?.entity_id;
  };

  result.status = find("status");
  result.power_flow = find("power_flow");
  result.surplus = find("surplus_for_car");
  result.target_current = find("target_current");
  result.controlling = find("controlling");
  result.battery_hold = find("battery_hold");
  result.charging_mode = find("charging_mode");
  result.battery_hold_mode = find("battery_hold_mode");
  result.smart_control = find("smart_control");
  result.auto_phase = find("auto_phase");
  result.manual_charge = find("manual_charge");
  result.start_now = find("start_now");
  result.manual_current = find("manual_current");
  result.manual_phases = find("manual_phases");
  result.battery_reserve_soc = find("battery_reserve_soc");
  result.target_energy = find("target_energy");
  result.departure = find("departure");
  result.max_current = find("max_current");
  result.min_current = find("min_current");
  result.price_forecast = find("price_forecast");
  result.cheap_price = find("cheap_price");

  result.peak_window_power = find("peak_window_power");
  result.monthly_peak = find("monthly_peak");
  result.rolling_grid_power = find("rolling_grid_power");
  result.peak_status = find("peak_status");
  result.peak_guard_active = find("peak_guard_active");
  result.peak_guard = find("peak_guard");
  result.peak_follow_month = find("peak_follow_month");
  result.grid_charge = find("grid_charge");
  result.peak_soft_limit = find("peak_soft_limit");
  result.peak_target_limit = find("peak_target_limit");
  result.peak_hard_limit = find("peak_hard_limit");
  result.peak_month_buffer = find("peak_month_buffer");
  result.shaving_reserve_soc = find("shaving_reserve_soc");
  result.peak_min_soc = find("peak_min_soc");
  result.grid_setpoint = find("grid_setpoint");
  result.cheap_charge_power = find("cheap_charge_power");
  result.bright_day_target_soc = find("bright_day_target_soc");
  result.dark_day_target_soc = find("dark_day_target_soc");
  result.peak_ready_soc = find("peak_ready_soc");
  result.stock_up = find("stock_up");
  result.stock_up_target_soc = find("stock_up_target_soc");
  result.reset_monthly_peak = find("reset_monthly_peak");
  result.active_transaction = find("active_transaction");
  result.last_session_energy = find("last_session_energy");
  result.selected_tag = find("selected_tag");

  result.tag_energy = entries
    .filter(
      (e) =>
        e.translation_key === "tag_energy" ||
        e.entity_id.split(".")[1]?.includes("_tag_energy_"),
    )
    .map((e) => e.entity_id)
    .sort();

  return result;
}
