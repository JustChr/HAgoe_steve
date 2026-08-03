"""Minimal Home Assistant websocket client — long-term statistics puller."""

from __future__ import annotations

import asyncio
import json
import os
import pathlib
import sys

import aiohttp

#: Point this at your own instance: set ``HA_URL``, and supply a long-lived access token
#: (Profile → Security) either in ``HA_TOKEN`` or in ``token.txt`` beside this file.
#: Both the token file and the pulled data snapshots are git-ignored.
BASE = os.environ.get("HA_URL", "http://homeassistant.local:8123").rstrip("/")


def _token() -> str:
    from_env = os.environ.get("HA_TOKEN")
    if from_env:
        return from_env.strip()
    path = pathlib.Path(__file__).with_name("token.txt")
    if not path.exists():
        raise SystemExit(
            "No Home Assistant token. Set HA_TOKEN, or write one to tools/sim/token.txt."
        )
    return path.read_text().strip()


TOKEN = _token()


class HA:
    def __init__(self, ws):
        self.ws = ws
        self._id = 0

    async def cmd(self, **payload):
        self._id += 1
        payload["id"] = self._id
        await self.ws.send_json(payload)
        while True:
            msg = await self.ws.receive_json()
            if msg.get("id") == self._id and msg.get("type") == "result":
                if not msg.get("success"):
                    raise RuntimeError(msg.get("error"))
                return msg.get("result")


async def connect(fn):
    async with aiohttp.ClientSession() as s:
        async with s.ws_connect(f"{BASE}/api/websocket", heartbeat=30) as ws:
            await ws.receive_json()  # auth_required
            await ws.send_json({"type": "auth", "access_token": TOKEN})
            ok = await ws.receive_json()
            if ok.get("type") != "auth_ok":
                raise SystemExit(f"auth failed: {ok}")
            return await fn(HA(ws))


async def stats(ha, ids, start, end, period="hour", types=("mean", "min", "max", "sum")):
    return await ha.cmd(
        type="recorder/statistics_during_period",
        start_time=start, end_time=end,
        statistic_ids=list(ids), period=period, types=list(types),
    )


async def list_ids(ha):
    return await ha.cmd(type="recorder/list_statistic_ids")
