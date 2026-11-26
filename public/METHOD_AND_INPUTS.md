# Method and inputs

The system is proprietary. It uses Qwen3.8-Max to autonomously select appropriate skills from a fixed skill library based on public natural-language instructions and robot embodiment. The implementation, architecture, full prompts, skill contents and controller details are not provided.

The skill library and selection mechanism were fixed before evaluation. The system was adapted to LADDER during development using observed outcomes and human video analysis. Each episode uses a new process and fresh memory. No hidden task ID, simulator object pose, evaluator success label or scoring trace is supplied to the policy. The inputs are public instructions, RGB, depth, camera calibration and proprioception. Scoring traces appear only in evaluation logs and offline score extraction.
