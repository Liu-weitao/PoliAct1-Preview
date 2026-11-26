# Native log extraction

The evaluated logs contain public subtask text and native goal traces, but omit `goal_objects`, which the upstream extractor expects. A separate offline extraction view reconstructs this field from the public subtask text. The original logs are preserved byte for byte. Relay stages retain their shared object identities. In `comp_route_10`, the two public orange instances at goal indices 3 and 8 are distinct objects. Every extracted success label, step count and ordered subgoal total is checked against the native result. No extraction data enter the agent.

The actual evaluated LADDER commit is `d645441a716595cce2ef9fb96abf2a324dc25b21`. The unchanged archived upstream packaging/checking tool is from `bef9e2276173d5d5fbe667a4ef687884be9c9f33`, which supports Lite-only data.
