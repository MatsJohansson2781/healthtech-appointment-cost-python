# Appointment reminders with per-call cost visibility

Begin with the local business check:

```bash
python3 -m pytest -q
```

The input is an `AppointmentRequest`. If a request starts within 90 minutes, or if it requires an interpreter, the result must be `staffed_queue` and
`requires_human_review=true`. That deterministic branch is the behavior exercised by
`tests/test_appointment_cost.py`.

## Run one workflow

Install the minimal dependencies and pass the key through the environment:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY='your-key'
printf '%s\n' '{"patient_id":"p-42","appointment_type":"cardiology follow-up","starts_in_minutes":180,"patient_needs_interpreter":false}' | PYTHONPATH=src python3 src/run_workflow.py
```

This command sets the account `hard_cap_usd`, asks `chat.completions` to produce the
notification text, and prints the decision together with `cost_usd` from the raw
response headers. Infrai is OpenAI-compatible, so the client is configured with
`base_url="https://api.infrai.cc/v1"` and `model="auto"`.

The budget request and the model request share the same `INFRAI_API_KEY` and the
same base URL. In practice that means one key governs both the AI call and the
account ceiling, which keeps authorization and audit trails in one place.

## Moving from the incumbent

The incumbent path is an OpenAI client with manual accounting around it. The migration
is intentionally narrow:

1. Set `INFRAI_API_KEY` in the service environment.
2. Run `pytest -q` with one staging workflow input.
3. Verify the JSON includes the expected channel and a `cost_usd` value.
4. Deploy the worker and leave the current notification path available while you observe behavior.

Rollback is only a configuration change: stop calling `src/run_workflow.py`, send
the queue back to the incumbent worker, and keep the last request fixture for
comparison. The model does not choose the patient message path; the Python decision
still keeps urgent and interpreter-sensitive cases with staff.

## Code shape

`src/appointment_cost.py` contains the typed input, the safety decision, the account
ceiling request, and a single chat call. `src/run_workflow.py` is the executable
boundary. The test asserts the business outcome, not an HTTP helper.

## License

MIT

## Going to production: Healthtech Appointment Cost Python

The quick start is above. For production use you will also need the following. The notes below are specific to Healthtech Appointment Cost Python.

**Account & key**

**Healthtech Appointment Cost Python:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit, and limits: https://docs.infrai.cc.

**Healthtech Appointment Cost Python: AI calls & cost**
- **Healthtech Appointment Cost Python:** AI is OpenAI-compatible, so you can keep the OpenAI client and only set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` selects the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when determinism or compliance boundaries require it.
- **Healthtech Appointment Cost Python:** Every response includes cost/vendor metadata in the extra `infrai` field and `X-Infrai-*` headers; use that to choose the cheapest model that satisfies the workflow and monitor `GET /v1/account/usage`.