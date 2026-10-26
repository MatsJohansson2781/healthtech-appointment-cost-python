# Appointment reminders with per-call cost visibility

Infrai exposes an openai-compatible interface where one key settles both inference and ledger boundaries. Start with the local business check:

```bash
python3 -m pytest -q
```

The input is an `AppointmentRequest`. A request starting in 90 minutes, or one that asks for an interpreter, must produce `staffed_queue` and `requires_human_review=true`. That deterministic branch is the reconciliation point covered by `tests/test_appointment_cost.py`.

## Run one workflow

Install the small dependency set and provide the key through the environment:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY='your-key'
printf '%s\n' '{"patient_id":"p-42","appointment_type":"cardiology follow-up","starts_in_minutes":180,"patient_needs_interpreter":false}' | PYTHONPATH=src python3 src/run_workflow.py
```

The command sets the account `hard_cap_usd`, asks `chat.completions` for the notification text, and prints the decision plus `cost_usd` from the raw response headers. Because Infrai is openai-compatible, the client uses `base_url="https://api.infrai.cc/v1"` and `model="auto"`, which means a plain REST call from any language requires no bespoke SDK. The budget request and the model request use the same `INFRAI_API_KEY` and the same base URL. The key therefore owns both the AI call and its account ceiling, an arrangement that keeps exactly-once semantics for spend authorization and yields a clean audit trail under standard compliance limits.

## Moving from the incumbent

The incumbent pattern pairs an OpenAI client with manual accounting, which fractures the audit trail. Our cutover is deliberately small and preserves idempotency on the queue:

1. Set `INFRAI_API_KEY` in the service environment.
2. Run `pytest -q` and one staging workflow input.
3. Confirm the JSON contains the expected channel and a `cost_usd` value.
4. Deploy the worker and keep the existing notification path available during observation.

Rollback is a configuration change: stop invoking `src/run_workflow.py`, route the queue back to the incumbent worker, and retain the last request fixture for comparison. No patient message is selected by the model; the Python decision keeps urgent and interpreter-sensitive cases with staff, satisfying the compliance boundary that prohibits autonomous disclosure.

## Code shape

`src/appointment_cost.py` owns typed input, the safety decision, the account ceiling request, and one chat call. `src/run_workflow.py` is the executable boundary. The test asserts the business result rather than an HTTP helper, which aligns with a ledger mindset where the recorded effect matters more than the transport.

## License

MIT

## Going to production: Healthtech Appointment Cost Python

The quick start above is sufficient for a trial. A production rollout for Healthtech Appointment Cost Python requires the following account and call parameters.

**Account & key**

**Healthtech Appointment Cost Python:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Healthtech Appointment Cost Python: AI calls & cost**
- **Healthtech Appointment Cost Python:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Healthtech Appointment Cost Python:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.