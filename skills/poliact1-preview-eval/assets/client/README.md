# PoliAct1-Preview

PoliAct1-Preview exposes a general-purpose robotic manipulation model API through a unified HTTP observations-to-actions interface. This repository contains its public evaluation client for LADDER. The evaluator sends public robot observations and executes the returned actions. The hosted service runs the complete system, including Qwen3.8-Max inference; no model-provider credentials are needed.

The current documented evaluation configuration targets LADDER-Lite (10 tasks, 112 episodes). This release does not establish generalization or performance beyond that scope.

| Item | Value |
|---|---|
| Recommended API | https://uat-open.qj-robots.com/ladder |
| Direct-IP fallback | https://115.190.169.226:18443 |
| Agent entry point | `your_client.py:YourClass` |
| Default model | Qwen3.8-Max |
| Evaluation scope | LADDER-Lite: 10 tasks, 112 episodes |
| Capacity | Up to 32 active episodes |
| Access | Free self-service API keys, without manual approval |

## Connect

Use Python 3.10 or later. From the client directory:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-client.txt
python3 register_cli.py --url https://uat-open.qj-robots.com/ladder --access-file ../poliact1-access.json --accept-terms
export POLIACT1_PREVIEW_ACCESS_FILE="$(realpath ../poliact1-access.json)"
python3 verify_cli.py
```

Register once and reuse the access file. The file contains your API key; keep it private. Existing keys can instead be supplied with `POLIACT1_PREVIEW_API_KEY` and `POLIACT1_PREVIEW_URL`.

Keep `/ladder` in the recommended base URL. It uses standard HTTPS certificate trust. The direct-IP fallback has no path prefix and automatically uses the bundled [server-ca.crt](server-ca.crt), which expires on **2026-12-25 at 09:57:25 UTC**.

## Run LADDER-Lite

Prepare the official LADDER environments and assets at commit `d645441a716595cce2ef9fb96abf2a324dc25b21`. Use the native Python environment for each simulator suite.

From the client directory, record the absolute agent path:

```bash
export POLIACT1_CLIENT="$(pwd)/your_client.py"
```

Then run these commands from your LADDER checkout, keeping the access-file variable exported:

```bash
scripts/eval.sh --suite robolab_long --task lite --agent "$POLIACT1_CLIENT:YourClass" --name poliact1_preview --episodes 8 --output out/poliact1-preview
scripts/eval.sh --suite robotarena_long --task lite --agent "$POLIACT1_CLIENT:YourClass" --name poliact1_preview --output out/poliact1-preview
scripts/eval.sh --suite simplerenv_long --task lite --agent "$POLIACT1_CLIENT:YourClass" --name poliact1_preview --episodes 24 --output out/poliact1-preview
```

The three suites contain 32, 32 and 48 episodes. The agent implements `run(arm)`, handles both native end-effector and joint actions, and closes its session when the episode ends.

## HTTP interface

| Operation | Method and path |
|---|---|
| Health | `GET /healthz` |
| Access limits | `GET /v1/access-policy` |
| Register | `POST /v1/keys` with `{"accept_terms":true}` |
| Service information / usage | `GET /v1/info`, `GET /v1/usage` |
| Create episode | `POST /v1/sessions` |
| Submit observation | `POST /v1/sessions/{id}/step` |
| Poll action | `GET /v1/sessions/{id}/actions?sequence=N&wait_s=25` |
| End episode | `POST /v1/sessions/{id}/end` |

Paths are relative to the base URL. Authenticated calls use `X-API-Key` or `Authorization: Bearer`. The service provides its HTTP schema at `GET /openapi.json`.

The client sends the original instruction and native observations to the service, preserving their coordinates. The simulator controls episode termination. For another simulator, implement the observation/action adapter described in the repository root EXTERNAL_ENVIRONMENTS.md.

Create an episode using the same call for any instruction:

```python
session = api.create(
    instruction="Please pick up the fork and place it inside the pan.",
    robot="widowx",
    max_steps=100,
)
```

Inputs are public instructions, robot embodiment, calibrated RGB-D and proprioception. Outputs are an end-effector pose or joint targets, with a gripper command. The included [agent](ladder_remote_agent.py) performs the observation/action loop.

HTTP 202 means the action is pending. Poll the same sequence and execute each returned action once. The client reconnects after transient failures and has no overall action-wait deadline by default. Individual HTTP requests use a 45-second timeout; server long polls last up to 25 seconds.

## Access limits and license

The service allows 32 active sessions, 128 new sessions per key per UTC day, and 256 globally per UTC day. Keys last 30 days. Registration allows 5 new keys per source IP per hour and 60 globally per hour. HTTP 429 provides `Retry-After`; `/v1/access-policy` lists current limits.

The distributed client and documentation use the [MIT license](LICENSE). The hosted implementation remains private. This release uses the fixed Qwen3.8-Max model.
