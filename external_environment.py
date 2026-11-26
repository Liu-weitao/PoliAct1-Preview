"""Run an environment adapter through the PoliAct1-Preview HTTP API."""
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from protocol import encode_observation


def run_external_episode(client, adapter, *, instruction, robot, max_steps=200):
    session = client.create(instruction=instruction, robot=robot, max_steps=max_steps)
    sid, actions, reason = session['session_id'], 0, 'client_closed'
    try:
        for step in range(max_steps):
            observed = adapter.observe()
            if observed is None:
                reason = 'native_episode_over'
                break
            obs = dict(observed, instruction=instruction, robot=robot, step=step)
            reply = client.step(sid, step, encode_observation(obs))
            if reply['status'] != 'action':
                break
            action = reply['action']
            if action['type'] not in ('eef_pose', 'joint_position'):
                raise ValueError('Unsupported action type.')
            # Both action types include the end-effector target.
            adapter.execute(np.asarray(action['eef_pose'], dtype=float), float(action['gripper']))
            actions += 1
        else:
            reason = 'native_episode_over'
        return dict(session_id=sid, actions_executed=actions)
    except BaseException as error:
        if type(error).__name__ == 'EpisodeOver':
            reason = 'native_episode_over'
        raise
    finally:
        unwinding = sys.exc_info()[0] is not None
        try:
            client.end(sid, reason)
        except Exception:
            if not unwinding:
                raise
