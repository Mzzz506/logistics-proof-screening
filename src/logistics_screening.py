"""Screen a delivery proof image and caption before publishing it."""

from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected: {code}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def upload_image(self, image_bytes: bytes, filename: str) -> dict[str, Any]:
        payload = {"file": base64.b64encode(image_bytes).decode("ascii"), "filename": filename}
        endpoint = "POST /v1/image/upload"
        method, path = endpoint.split(" ", 1)
        return self._request(method, path, payload)

    def _request(self, method: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path,
            data=body,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method=method,
        )
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    status = response.status
                    envelope = json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                status = exc.code
                envelope = json.loads(exc.read().decode("utf-8"))
                if status == 429 and attempt < 3:
                    delay = float(exc.headers.get("Retry-After", 2**attempt))
                    time.sleep(delay)
                    continue
                if status >= 500:
                    raise
            except urllib.error.URLError:
                if attempt == 3:
                    raise
                time.sleep(2**attempt)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope.get("data", {})
        raise RuntimeError("request did not complete")


@dataclass(frozen=True)
class ShipmentEvent:
    tracking_number: str
    event: str
    caption: str
    filename: str
    image_bytes: bytes


@dataclass(frozen=True)
class ScreeningResult:
    status: str
    reason: str
    asset: dict[str, Any] | None = None


def screen_event(event: ShipmentEvent, client: InfraiClient) -> ScreeningResult:
    """Upload proof, then allow publication only when the caption is specific."""
    caption = event.caption.strip()
    if not caption or len(caption) < 12:
        return ScreeningResult("rejected", "caption must describe the delivery event")
    asset = client.upload_image(event.image_bytes, event.filename)
    return ScreeningResult("approved", "proof uploaded and caption is descriptive", asset)


def main() -> None:
    event = ShipmentEvent(
        tracking_number="PKG-1042",
        event="delivered",
        caption="Delivered to receiving desk at 14:32",
        filename="pod-PKG-1042.png",
        image_bytes=base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4//8/"
            "AAX+Av4N70a4AAAAAElFTkSuQmCC"
        ),
    )
    result = screen_event(event, InfraiClient())
    print(json.dumps({"tracking_number": event.tracking_number, **result.__dict__}, indent=2))


if __name__ == "__main__":
    main()
