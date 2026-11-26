"""LADDER HTTP agent: forward public observations and execute returned actions."""
import os
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from client import Client
from protocol import encode_observation
from access import client_settings


class PoliAct1PreviewRemoteAgent:
    def run(self, arm):
        initial = arm.observation
        robot = str(getattr(initial['robot'], 'value', initial['robot'])).rsplit('.', 1)[-1].lower()
        ceiling = int(os.environ.get('LADDER_POLIACT1_PREVIEW_MAX_STEPS', '10000'))
        if not 1 <= ceiling <= 10000:
            raise ValueError('Action ceiling must be between 1 and 10000.')
        url, key = client_settings()
        client = Client(url, key, os.environ.get('POLIACT1_PREVIEW_CA'))
        session = None
        last = None
        native_end = False

        def public(obs):
            cameras = obs['depth']
            return dict(instruction=obs['instruction'], robot=robot, step=obs['step'],
                eef_pose=obs['eef_pose'], joints=obs['joints'], gripper=obs['gripper'],
                images={name: obs['images'][name] for name in cameras},
                depth={name: cameras[name] for name in cameras})

        def execute(action):
            if action['type'] == 'joint_position':
                if robot != 'franka':
                    raise ValueError('Native joint actions require the Franka controller.')
                from ladder.components.inference.api.core.action import JointAnglesAction, ManipulatorAction
                return arm._episode.act(ManipulatorAction(
                    arm_action=JointAnglesAction(angles=np.asarray(action['joint_targets'], dtype=np.float32)),
                    gripper_action=float(action['gripper'])))
            if action['type'] != 'eef_pose':
                raise ValueError('Unsupported action type.')
            return arm.step(np.asarray(action['eef_pose'], dtype=np.float64), float(action['gripper']))

        try:
            obs = public(initial)
            session = client.create(instruction=obs['instruction'], robot=robot,
                                    max_steps=ceiling)['session_id']
            sequence = 0
            while True:
                reply = client.step(session, sequence, encode_observation(obs))
                if reply['status'] != 'action':
                    # The native simulator remains authoritative for termination.
                    if last is None:
                        last = dict(type='eef_pose', eef_pose=np.asarray(obs['eef_pose']).tolist(),
                                    gripper=obs['gripper'])
                    while True:
                        execute(last)
                last = reply['action']
                execute(last)
                obs = public(arm.observation)
                sequence += 1
        except BaseException as error:
            native_end = type(error).__name__ == 'EpisodeOver'
            raise
        finally:
            if session:
                try:
                    client.end(session, 'native_episode_over' if native_end else 'client_closed')
                except Exception:
                    pass
