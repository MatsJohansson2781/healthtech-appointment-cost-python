"""Run one appointment notification from JSON-shaped input."""

import json
import sys

from appointment_cost import AppointmentRequest, create_notification, configure_budget


def main() -> None:
    request = AppointmentRequest.model_validate_json(sys.stdin.read())
    configure_budget(10.0, "monthly")
    result = create_notification(request)
    print(json.dumps({
        "channel": result.decision.channel,
        "requires_human_review": result.decision.requires_human_review,
        "message": result.message,
        "cost_usd": result.cost_usd,
    }))


if __name__ == "__main__":
    main()
