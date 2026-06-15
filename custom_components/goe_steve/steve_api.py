"""Thin async client + pure parsing for the SteVe OCPP server REST API.

Per the locked architecture (see project memory), SteVe is used for
**authorization and metering only** — HA regulates charge power directly via the
go-e local API. This module therefore reads transactions/tags and offers
authorize/block plus best-effort remote start/stop, nothing power-related.

It is deliberately free of any Home Assistant imports: the dataclasses and the
``parse_*`` / ``aggregate_*`` helpers are pure and unit-tested without HA (see
``tests/test_steve_api.py``); :class:`SteVeApiClient` only needs an
``aiohttp.ClientSession`` injected by the caller.

API shape (SteVe v1). Auth is HTTP Basic on the ``/api/**`` chain: the username
is a SteVe *web user* (default ``admin``) and the password is that user's
*API password* — seeded from ``webapi.value`` (web-api-secret) in SteVe's
main.properties, distinct from the web-login password and unrelated to the
``webapi.key`` / ``STEVE-API-KEY`` header (unused by this chain in SteVe 3.13.x):
    GET  {base}/steve/api/v1/ocppTags
    GET  {base}/steve/api/v1/transactions?ocppIdTag=&type=ACTIVE&from=&to=
    PUT  {base}/steve/api/v1/ocppTags/{ocppTagPk}        (authorize/block)
    POST {base}/steve/api/v1/operations/RemoteStartTransaction  {chargeBoxIdList:[id], connectorId?, idTag}
    POST {base}/steve/api/v1/operations/RemoteStopTransaction   {chargeBoxIdList:[id], transactionId}
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime

try:  # aiohttp is only needed for the HTTP client, not the pure parsing helpers
    import aiohttp
    from aiohttp import BasicAuth
except ModuleNotFoundError:  # keeps this module importable in HA-free unit tests
    aiohttp = None  # type: ignore[assignment]
    BasicAuth = None  # type: ignore[assignment]

_LOGGER = logging.getLogger(__name__)

# A tag whose maximum concurrent-transaction count is zero cannot start a
# charge — that is how SteVe expresses "blocked". Authorizing restores the
# "unlimited" sentinel.
BLOCKED_MAX_ACTIVE: int = 0
UNLIMITED_MAX_ACTIVE: int = -1


class SteVeApiError(Exception):
    """Raised when a SteVe API call fails (network, auth, or HTTP status)."""


# --- Pure data model + parsing (HA-free, unit-tested) ------------------------------


@dataclass(slots=True)
class SteVeTag:
    """One OCPP id-tag (RFID card / user) as known to SteVe."""

    pk: int | None
    id_tag: str
    blocked: bool = False
    in_transaction: bool = False
    parent_id_tag: str | None = None
    expiry: datetime | None = None
    note: str | None = None
    max_active_count: int | None = None


@dataclass(slots=True)
class SteVeTransaction:
    """One charging session. ``energy_kwh`` is None while still open."""

    id: int | None
    charge_box_id: str | None
    id_tag: str | None
    start: datetime | None = None
    stop: datetime | None = None
    start_value_wh: float | None = None
    stop_value_wh: float | None = None

    @property
    def is_active(self) -> bool:
        return self.stop is None and self.stop_value_wh is None

    @property
    def energy_kwh(self) -> float | None:
        if self.start_value_wh is None or self.stop_value_wh is None:
            return None
        return max(0.0, self.stop_value_wh - self.start_value_wh) / 1000.0


@dataclass(slots=True)
class SteVeData:
    """Snapshot pushed to entities by the SteVe coordinator each poll."""

    tags: list[SteVeTag] = field(default_factory=list)
    transactions: list[SteVeTransaction] = field(default_factory=list)
    active: list[SteVeTransaction] = field(default_factory=list)
    energy_by_tag: dict[str, float] = field(default_factory=dict)
    last_session: SteVeTransaction | None = None


def _parse_dt(value: object) -> datetime | None:
    """Parse a SteVe ISO-8601 timestamp tolerantly (handles a trailing ``Z``)."""
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _parse_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def parse_tag(raw: dict) -> SteVeTag | None:
    """Parse one ``/ocppTags`` item, tolerant of field-name variations."""
    if not isinstance(raw, dict):
        return None
    id_tag = raw.get("idTag") or raw.get("ocppIdTag") or raw.get("id_tag")
    if not id_tag:
        return None
    max_active = raw.get("maxActiveTransactionCount")
    blocked = bool(raw.get("blocked")) or (
        isinstance(max_active, int) and max_active == BLOCKED_MAX_ACTIVE
    )
    return SteVeTag(
        pk=raw.get("ocppTagPk") or raw.get("id"),
        id_tag=str(id_tag),
        blocked=blocked,
        in_transaction=bool(raw.get("inTransaction")),
        parent_id_tag=raw.get("parentIdTag"),
        expiry=_parse_dt(raw.get("expiryDate")),
        note=raw.get("note"),
        max_active_count=max_active if isinstance(max_active, int) else None,
    )


def parse_transaction(raw: dict) -> SteVeTransaction | None:
    """Parse one ``/transactions`` item, tolerant of field-name variations."""
    if not isinstance(raw, dict):
        return None
    return SteVeTransaction(
        id=raw.get("id") or raw.get("transactionPk"),
        charge_box_id=raw.get("chargeBoxId"),
        id_tag=raw.get("ocppIdTag") or raw.get("idTag"),
        start=_parse_dt(raw.get("startTimestamp") or raw.get("startTimestampFormatted")),
        stop=_parse_dt(raw.get("stopTimestamp") or raw.get("stopTimestampFormatted")),
        start_value_wh=_parse_float(raw.get("startValue")),
        stop_value_wh=_parse_float(raw.get("stopValue")),
    )


def parse_tags(raw: object) -> list[SteVeTag]:
    if not isinstance(raw, (list, tuple)):
        return []
    return [tag for item in raw if (tag := parse_tag(item)) is not None]


def parse_transactions(raw: object) -> list[SteVeTransaction]:
    if not isinstance(raw, (list, tuple)):
        return []
    return [tx for item in raw if (tx := parse_transaction(item)) is not None]


def aggregate_energy_by_tag(
    transactions: list[SteVeTransaction],
) -> dict[str, float]:
    """Total delivered energy (kWh) per id-tag across the given transactions."""
    totals: dict[str, float] = {}
    for tx in transactions:
        energy = tx.energy_kwh
        if energy is None or not tx.id_tag:
            continue
        totals[tx.id_tag] = totals.get(tx.id_tag, 0.0) + energy
    return totals


def latest_completed(
    transactions: list[SteVeTransaction],
) -> SteVeTransaction | None:
    """The most recently finished session (by stop time, then start time)."""
    finished = [tx for tx in transactions if tx.stop is not None]
    if not finished:
        return None
    return max(
        finished,
        key=lambda tx: (tx.stop or datetime.min, tx.start or datetime.min),
    )


def build_steve_data(
    tags_raw: object, transactions_raw: object
) -> SteVeData:
    """Assemble a :class:`SteVeData` snapshot from raw API payloads."""
    transactions = parse_transactions(transactions_raw)
    active = [tx for tx in transactions if tx.is_active]
    return SteVeData(
        tags=parse_tags(tags_raw),
        transactions=transactions,
        active=active,
        energy_by_tag=aggregate_energy_by_tag(transactions),
        last_session=latest_completed(transactions),
    )


# --- HTTP client -------------------------------------------------------------------


def normalize_base_url(url: str) -> str:
    """Return the ``…/steve/api/v1`` base from a user-entered SteVe root URL.

    Accepts ``http://host:8080``, ``…/steve`` or the full API path and avoids
    duplicating the ``/steve`` segment.
    """
    base = url.strip().rstrip("/")
    for suffix in ("/steve/api/v1", "/steve/api", "/steve"):
        if base.endswith(suffix):
            base = base[: -len(suffix)]
            break
    return f"{base}/steve/api/v1"


class SteVeApiClient:
    """Minimal async wrapper over the SteVe v1 REST API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        url: str,
        username: str,
        password: str,
        *,
        timeout: float = 10.0,
    ) -> None:
        self._session = session
        self._base = normalize_base_url(url)
        self._auth = BasicAuth(username, password)
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    async def _request(
        self, method: str, path: str, *, json_body: dict | None = None
    ) -> object:
        url = f"{self._base}/{path.lstrip('/')}"
        try:
            async with self._session.request(
                method, url, json=json_body, auth=self._auth, timeout=self._timeout
            ) as resp:
                if resp.status == 401:
                    raise SteVeApiError("SteVe rejected the credentials (401)")
                if resp.status >= 400:
                    body = await resp.text()
                    raise SteVeApiError(
                        f"SteVe {method} {path} → HTTP {resp.status}: {body[:200]}"
                    )
                # Tolerate empty bodies (common on PUT/POST) and lax content types.
                text = await resp.text()
                if not text.strip():
                    return None
                try:
                    return json.loads(text)
                except ValueError:
                    return None
        except aiohttp.ClientError as err:
            raise SteVeApiError(f"SteVe request failed: {err}") from err
        except TimeoutError as err:
            raise SteVeApiError("SteVe request timed out") from err

    async def async_get_tags(self) -> list[SteVeTag]:
        return parse_tags(await self._request("GET", "ocppTags"))

    async def async_get_transactions(
        self, *, id_tag: str | None = None, active_only: bool = False
    ) -> list[SteVeTransaction]:
        params = []
        if id_tag:
            params.append(f"ocppIdTag={id_tag}")
        if active_only:
            params.append("type=ACTIVE")
        query = f"?{'&'.join(params)}" if params else ""
        return parse_transactions(await self._request("GET", f"transactions{query}"))

    async def async_fetch_data(self) -> SteVeData:
        """One poll: tags + transactions → an assembled snapshot."""
        tags = await self._request("GET", "ocppTags")
        transactions = await self._request("GET", "transactions")
        return build_steve_data(tags, transactions)

    async def async_set_tag_blocked(self, id_tag: str, blocked: bool) -> None:
        """Block or authorize a tag by toggling its max active-transaction count.

        Read-modify-write: fetch the tag to learn its primary key, then PUT it
        back with the changed limit so we don't clobber other fields.
        """
        tag = await self._find_tag(id_tag)
        if tag is None or tag.pk is None:
            raise SteVeApiError(f"Unknown SteVe id-tag '{id_tag}'")
        body = {
            "idTag": tag.id_tag,
            "parentIdTag": tag.parent_id_tag,
            "note": tag.note,
            "maxActiveTransactionCount": (
                BLOCKED_MAX_ACTIVE if blocked else UNLIMITED_MAX_ACTIVE
            ),
        }
        await self._request("PUT", f"ocppTags/{tag.pk}", json_body=body)

    async def _find_tag(self, id_tag: str) -> SteVeTag | None:
        for tag in await self.async_get_tags():
            if tag.id_tag == id_tag:
                return tag
        return None

    async def async_remote_start(
        self, charge_box_id: str, connector_id: int, id_tag: str
    ) -> None:
        # SteVe models the target as a one-element ``chargeBoxIdList``; a zero/None
        # connector means "no specific connector", so it is omitted entirely.
        body: dict = {"chargeBoxIdList": [charge_box_id], "idTag": id_tag}
        if connector_id:
            body["connectorId"] = connector_id
        await self._request(
            "POST", "operations/RemoteStartTransaction", json_body=body
        )

    async def async_remote_stop(
        self, charge_box_id: str, transaction_id: int
    ) -> None:
        await self._request(
            "POST",
            "operations/RemoteStopTransaction",
            json_body={
                "chargeBoxIdList": [charge_box_id],
                "transactionId": transaction_id,
            },
        )
