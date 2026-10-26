from appointment_cost import AppointmentRequest, decide_notification


def test_near_term_interpreter_request_stays_with_staff() -> None:
    request = AppointmentRequest(
        patient_id="p-42",
        appointment_type="cardiology follow-up",
        starts_in_minutes=90,
        patient_needs_interpreter=True,
    )

    decision = decide_notification(request)

    assert decision.channel == "staffed_queue"
    assert decision.requires_human_review is True
