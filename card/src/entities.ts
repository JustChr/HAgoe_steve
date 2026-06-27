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
  charging_mode?: string;
  battery_policy?: string;
  smart_control?: string;
  auto_phase?: string;
  manual_charge?: string;
  manual_current?: string;
  manual_phases?: string;
  battery_reserve_soc?: string;
  battery_floor_soc?: string;
  target_energy?: string;
  departure?: string;
  max_current?: string;
  min_grid_floor?: string;
  price_forecast?: string;
  cheap_price?: string;
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
  result.charging_mode = find("charging_mode");
  result.battery_policy = find("battery_policy");
  result.smart_control = find("smart_control");
  result.auto_phase = find("auto_phase");
  result.manual_charge = find("manual_charge");
  result.manual_current = find("manual_current");
  result.manual_phases = find("manual_phases");
  result.battery_reserve_soc = find("battery_reserve_soc");
  result.battery_floor_soc = find("battery_floor_soc");
  result.target_energy = find("target_energy");
  result.departure = find("departure");
  result.max_current = find("max_current");
  result.min_grid_floor = find("min_grid_floor");
  result.price_forecast = find("price_forecast");
  result.cheap_price = find("cheap_price");
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
