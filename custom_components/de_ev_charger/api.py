"""Минимальный клиент Tuya Cloud OpenAPI (подпись HMAC-SHA256).
Minimal Tuya Cloud OpenAPI client (HMAC-SHA256 signing)."""
import hashlib
import hmac
import json
import time
import uuid

import aiohttp


class TuyaApiError(Exception):
    def __init__(self, code, msg):
        super().__init__(f"{code}: {msg}")
        self.code = code


class TuyaCloudApi:
    def __init__(self, session: aiohttp.ClientSession, access_id, access_secret, endpoint):
        self._session = session
        self._id = access_id
        self._secret = access_secret
        self._endpoint = endpoint
        self._token = None
        self._token_exp = 0.0

    def _headers(self, method, path, body, token=""):
        t = str(int(time.time() * 1000))
        nonce = uuid.uuid4().hex
        body_hash = hashlib.sha256(body.encode()).hexdigest()
        string_to_sign = f"{method}\n{body_hash}\n\n{path}"
        msg = self._id + token + t + nonce + string_to_sign
        sign = hmac.new(self._secret.encode(), msg.encode(), hashlib.sha256).hexdigest().upper()
        headers = {
            "client_id": self._id,
            "sign": sign,
            "t": t,
            "nonce": nonce,
            "sign_method": "HMAC-SHA256",
            "Content-Type": "application/json",
        }
        if token:
            headers["access_token"] = token
        return headers

    async def _raw(self, method, path, body=None, token=""):
        data = json.dumps(body) if body is not None else ""
        async with self._session.request(
            method,
            self._endpoint + path,
            headers=self._headers(method, path, data, token),
            data=data or None,
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            res = await resp.json(content_type=None)
        if not res.get("success"):
            raise TuyaApiError(res.get("code"), res.get("msg"))
        return res.get("result")

    async def _ensure_token(self, force=False):
        if not force and self._token and time.time() < self._token_exp - 60:
            return
        res = await self._raw("GET", "/v1.0/token?grant_type=1")
        self._token = res["access_token"]
        self._token_exp = time.time() + int(res["expire_time"])

    async def request(self, method, path, body=None):
        await self._ensure_token()
        try:
            return await self._raw(method, path, body, self._token)
        except TuyaApiError as err:
            # 1010/1011 - токен истёк / невалиден: обновить и повторить
            # 1010/1011 - token expired / invalid: refresh and retry
            if err.code in (1010, 1011):
                await self._ensure_token(force=True)
                return await self._raw(method, path, body, self._token)
            raise

    async def get_status(self, device_id) -> dict:
        res = await self.request("GET", f"/v1.0/iot-03/devices/{device_id}/status")
        return {item["code"]: item["value"] for item in res}

    async def send(self, device_id, code, value):
        await self.request(
            "POST",
            f"/v1.0/iot-03/devices/{device_id}/commands",
            {"commands": [{"code": code, "value": value}]},
        )
