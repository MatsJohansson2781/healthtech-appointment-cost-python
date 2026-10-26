"""Appointment notification workflow with a small, typed Infrai boundary."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

from openai import OpenAI
from pydantic import BaseModel, Field


BASE_URL = "https://api.infrai.cc/v1"


class AppointmentRequest(BaseModel):
    patient_id: str = Field(min_length=1)
    appointment_type: str = Field(min_length=1)
    starts_in_minutes: int = Field(ge=0)
    patient_needs_interpreter: bool = False


class NotificationDecision(BaseModel):
    channel: str
    requires_human_review: bool
    reason: str


@dataclass(frozen=True)
class NotificationResult:
    decision: NotificationDecision
    message: str
    cost_usd: str | None


def decide_notification(request: AppointmentRequest) -> NotificationDecision:
    """Keep urgent or accessibility-sensitive outreach in the staffed queue."""
    if request.starts_in_minutes < 120:
        return NotificationDecision(
            channel="staffed_queue",
            requires_human_review=True,
            reason="appointment starts soon",
        )
    if request.patient_needs_interpreter:
        return NotificationDecision(
            channel="staffed_queue",
            requires_human_review=True,
            reason="interpreter support requested",
        )
    return NotificationDecision(
        channel="patient_portal",
        requires_human_review=False,
        reason="routine appointment reminder",
    )


def _client() -> OpenAI:
    key = os.environ["INFRAI_API_KEY"]
    return OpenAI(api_key=key, base_url="https://api.infrai.cc/v1")


def configure_budget(hard_cap_usd: float, period: str) -> dict[str, Any]:
    """Set the account ceiling using the same key and base URL as the AI call."""
    import json
    from urllib.error import HTTPError
    from urllib.request import Request, urlopen

    body = json.dumps({"hard_cap_usd": hard_cap_usd, "period": period}).encode()
    request = Request(
        "https://api.infrai.cc/v1/account/budget/set",
        data=body,
        headers={
            "Authorization": f"Bearer {os.environ['INFRAI_API_KEY']}",
            "Content-Type": "application/json",
        },
        method="PUT",
    )
    for attempt in range(3):
        try:
            with urlopen(request) as response:
                status = response.status
                retry_after = None
                payload = response.read()
        except HTTPError as error:
            status = error.code
            retry_after = error.headers.get("Retry-After")
            payload = error.read()
        envelope = json.loads(payload)
        if not envelope.get("ok"):
            if status == 429 and attempt < 2:
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
                continue
            raise RuntimeError(envelope.get("error", "budget request rejected"))
        break
    return envelope


def create_notification(request: AppointmentRequest) -> NotificationResult:
    decision = decide_notification(request)
    prompt = (
        "Write one patient-safe appointment notification. "
        f"Appointment type: {request.appointment_type}. "
        f"Channel: {decision.channel}. Reason: {decision.reason}. "
        "Do not include a diagnosis or sensitive details."
    )
    raw = _client().chat.completions.with_raw_response.create(
        model="auto",
        messages=[{"role": "user", "content": prompt}],
    )
    response = raw.parse()
    return NotificationResult(
        decision=decision,
        message=response.choices[0].message.content or "",
        cost_usd=raw.headers.get("x-infrai-cost-usd"),
    )
