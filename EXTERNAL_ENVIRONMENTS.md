# Connect an environment

Use the existing API key and `https://uat-open.qj-robots.com/ladder`.
For LADDER, keep the `your_client.py:YourClass` entry point.

For another environment, implement `adapter.observe()` and
`adapter.execute(eef_pose, gripper)`. Reset the environment, then call:

```python
from access import client_settings
from client import Client
from external_environment import run_external_episode

url, key = client_settings()
run_external_episode(
    Client(url, key), adapter,
    instruction="Pick up the red block and place it on the tray.",
    robot="my_robot", max_steps=200,
)
```

`observe()` returns these values from one control frame, or `None` when finished:

| Field | Format |
| --- | --- |
| `eef_pose` | 4×4 controlled-end-effector-to-robot-base transform; translation in metres. |
| `joints` | 1–64 finite joint values, radians or metres. |
| `gripper` | Openness: 0 closed, 1 open. |
| `images` | Camera name → H×W×3 uint8 RGB. |
| `depth` | Same camera names → `depth_m`, `intrinsics`, `base_from_camera`. |

`depth_m` is registered H×W optical-Z depth in metres; invalid pixels may be NaN.
`intrinsics` is the matching 3×3 camera matrix. `base_from_camera` is a 4×4
optical-camera-to-robot-base transform, with optical axes X right, Y down, Z forward.

`execute()` applies the absolute end-effector target in the same frame convention
as `eef_pose`, plus the gripper command, then advances the
environment, and makes the next observation available. The helper handles the
HTTP session, encoding, polling and cleanup. Pass the instruction unchanged.
