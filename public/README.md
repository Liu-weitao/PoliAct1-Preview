# PoliAct1-Preview LADDER-Lite results

PoliAct1-Preview records 86 complete task successes out of 112 episodes. Under LADDER’s official three-suite equal-weight aggregation, task success is 75.7% and ordered subgoal completion is 76.9%. The system uses the hosted model service identified as qwen3.8-max.

See [TASK_SCORES.md](TASK_SCORES.md) and [EPISODE_INDEX.md](EPISODE_INDEX.md). There is one complete main-camera episode recording per episode in `videos/`, encoded as H.264/AVC MP4 (yuv420p) with faststart for playback compatibility. The original resolution, frame count, frame rate and presentation timeline are preserved; there is no trimming or speed change. Native logs, metrics and episode metadata are copied without modification into `native_results/`. All ordinary terminal failures are included.

The implementation is proprietary. Source, weights, full prompts, skill implementations, experience contents and API traces are excluded. The public results URL is the `public/` directory of this repository.
