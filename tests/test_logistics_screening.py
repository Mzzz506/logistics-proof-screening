import pytest

from src.logistics_screening import ScreeningResult, ShipmentEvent, screen_event


class FakeClient:
    def upload_image(self, image_bytes: bytes, filename: str):
        return {"id": "asset-1", "filename": filename}


def test_short_caption_is_rejected_before_upload():
    event = ShipmentEvent("PKG-1", "delivered", "done", "pod.jpg", b"bytes")
    assert screen_event(event, FakeClient()) == ScreeningResult(
        "rejected", "caption must describe the delivery event"
    )


def test_descriptive_caption_is_approved_and_uploads_proof():
    event = ShipmentEvent("PKG-2", "delivered", "Left at front desk for Ana", "pod.jpg", b"bytes")
    result = screen_event(event, FakeClient())
    assert result.status == "approved"
    assert result.asset["id"] == "asset-1"
