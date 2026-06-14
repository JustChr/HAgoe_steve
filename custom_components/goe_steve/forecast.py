"""Provider-agnostic parsing of electricity price forecasts.

Kept free of Home Assistant imports (like ``engine.py``) so it can be unit-tested
with nothing but ``pytest``. The coordinator passes HA's configured timezone in as
``default_tz`` so naive provider timestamps are interpreted the same way at runtime.
"""

from __future__ import annotations

from datetime import datetime, timezone, tzinfo

from .engine import PriceSlot

# Price keys we accept, in priority order, paired with the factor that normalizes
# the provider's unit to currency/kWh. First present key wins.
#   value/price/total/price_per_kwh : already currency/kWh (Nordpool, EnergyZero…)
#   price_ct_per_kwh                : ct/kWh  (EPEX Spot) → ×0.01
#   price_eur_per_mwh               : €/MWh   (EPEX Spot) → ×0.001
_PRICE_KEYS: tuple[tuple[str, float], ...] = (
    ("value", 1.0),
    ("price", 1.0),
    ("total", 1.0),
    ("price_per_kwh", 1.0),
    ("price_ct_per_kwh", 0.01),
    ("price_eur_per_mwh", 0.001),
)

_START_KEYS = ("start", "start_time", "from", "hour")


def _parse_dt(value: object) -> datetime | None:
    """Parse a provider timestamp (ISO string or datetime) into a datetime."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            # fromisoformat handles trailing 'Z' since 3.11; cover both anyway.
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def parse_forecast(
    raw: object, default_tz: tzinfo = timezone.utc
) -> list[PriceSlot]:
    """Tolerantly parse a provider forecast list into :class:`PriceSlot`.

    Accepts the common shapes: a list of dicts with ``start``/``value`` (Nordpool,
    EnergyZero) or ``start_time``/``price``/``total`` keys, plus EPEX Spot's
    ``price_ct_per_kwh``/``price_eur_per_mwh`` (normalized to currency/kWh). Naive
    timestamps are assumed to be in ``default_tz``; slots without a usable
    timestamp or price are skipped.
    """
    if not isinstance(raw, (list, tuple)):
        return []
    slots: list[PriceSlot] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        start = next((item[k] for k in _START_KEYS if item.get(k) is not None), None)
        price: object | None = None
        scale = 1.0
        for key, key_scale in _PRICE_KEYS:
            if item.get(key) is not None:
                price = item[key]
                scale = key_scale
                break
        if start is None or price is None:
            continue
        start = _parse_dt(start)
        if start is None:
            continue
        if start.tzinfo is None:  # interpret naive timestamps in the given tz
            start = start.replace(tzinfo=default_tz)
        try:
            slots.append(
                PriceSlot(
                    start=start.astimezone(timezone.utc), price=float(price) * scale
                )
            )
        except (ValueError, TypeError):
            continue
    return slots


def dedupe_slots(slots: list[PriceSlot]) -> list[PriceSlot]:
    """Sort by start time and drop duplicate timestamps (today/tomorrow overlap)."""
    seen: set[datetime] = set()
    out: list[PriceSlot] = []
    for slot in sorted(slots, key=lambda s: s.start):
        if slot.start in seen:
            continue
        seen.add(slot.start)
        out.append(slot)
    return out
