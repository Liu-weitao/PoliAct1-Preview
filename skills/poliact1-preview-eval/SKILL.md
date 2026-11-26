---
name: poliact1-preview-eval
description: Connect a LADDER evaluator to the PoliAct1-Preview observations-to-actions HTTP API using the included Python client.
---

# PoliAct1-Preview evaluation integration

Use the standalone client in [assets/client](assets/client). The hosted system includes Qwen3.8-Max inference; the evaluator runs the simulator.

1. Follow [the client README](assets/client/README.md) to register a free API key and run `verify_cli.py`. Use `https://uat-open.qj-robots.com/ladder`, retaining the path prefix. The direct-IP fallback uses the bundled CA certificate.
2. Run `your_client.py:YourClass` in the evaluator's LADDER environment. The README provides the three suite commands for all 112 Lite episodes.
3. For a custom integration, retrieve the HTTP schema from `GET /openapi.json`. Create one session per episode, then send public observations with increasing sequence numbers. Pass the instruction unchanged; the native simulator controls episode termination.
4. Keep one creation idempotency key across transport retries. On HTTP 202, poll the same sequence. Execute its action once before submitting the next observation. End the session in `finally`.

The client handles native end-effector and joint actions. It has no default overall action-wait deadline and respects `Retry-After`. The API uses Qwen3.8-Max; provider keys and model overrides are not needed.
