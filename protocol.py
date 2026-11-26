"""Public RGB-D protocol. Never deserialize pickle, paths or URLs from clients."""
import base64
import hashlib
import json
import math

import numpy as np

VERSION = 'poliact1-preview-rgbd-v1'
MAX_BODY = 48 * 1024 * 1024
MAX_ARRAY_BYTES = 32 * 1024 * 1024


class APIError(Exception):
    def __init__(self, status, code, message):
        self.status, self.code, self.message = status, code, message
        super().__init__(message)


def fields(value, required, optional=()):
    if not isinstance(value, dict) or set(value) - set(required) - set(optional) or not set(required) <= set(value):
        raise APIError(422, 'invalid_fields', 'Required fields missing or additional fields supplied.')
    return value


def integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise APIError(422, 'invalid_integer', 'Integer outside the documented range.')
    return value


def encode_array(value):
    a = np.ascontiguousarray(value)
    if a.dtype.kind == 'f':
        a = a.astype('<f4' if a.dtype.itemsize == 4 else '<f8')
    return dict(dtype=a.dtype.str, shape=list(a.shape), data_b64=base64.b64encode(a.tobytes()).decode('ascii'))


def decode_array(value, kind):
    fields(value, ('dtype', 'shape', 'data_b64'))
    allowed = {'rgb': {'|u1', 'uint8'}, 'depth': {'<f4', '<f8', 'float32', 'float64'}}[kind]
    if not isinstance(value['dtype'], str) or value['dtype'] not in allowed or not isinstance(value['shape'], list):
        raise APIError(422, 'array_dtype', 'Unsupported array dtype.')
    shape = value['shape']
    if len(shape) != (3 if kind == 'rgb' else 2):
        raise APIError(422, 'array_shape', 'Invalid image or depth shape.')
    for size in shape[:2]:
        integer(size, 1, 4096)
    if kind == 'rgb' and shape[2] != 3:
        raise APIError(422, 'array_shape', 'RGB must contain three channels.')
    dtype = np.dtype(value['dtype'])
    size = math.prod(shape) * dtype.itemsize
    if size > MAX_ARRAY_BYTES or not isinstance(value['data_b64'], str) or len(value['data_b64']) > (MAX_ARRAY_BYTES * 4 // 3 + 4):
        raise APIError(413, 'array_size', 'Array exceeds size limit.')
    try:
        raw = base64.b64decode(value['data_b64'], validate=True)
    except (ValueError, TypeError):
        raise APIError(422, 'array_base64', 'Invalid base64 array.') from None
    if len(raw) != size:
        raise APIError(422, 'array_size', 'Array shape and byte count disagree.')
    return np.frombuffer(raw, dtype=dtype).reshape(shape).copy()


def observation(value, public_observation, *, generic=False):
    fields(value, ('instruction', 'robot', 'step', 'eef_pose', 'joints', 'gripper', 'images', 'depth'))
    if not isinstance(value['instruction'], str) or not 1 <= len(value['instruction']) <= 16000:
        raise APIError(422, 'instruction', 'A public natural-language instruction is required.')
    integer(value['step'], 0, 1000000)
    if type(value['gripper']) not in (int, float) or not math.isfinite(value['gripper']):
        raise APIError(422, 'gripper', 'Gripper must be a finite openness fraction.')
    if not isinstance(value['images'], dict) or not isinstance(value['depth'], dict) or not 1 <= len(value['depth']) <= 8:
        raise APIError(422, 'cameras', 'One to eight calibrated RGB-D cameras are required.')
    if set(value['images']) != set(value['depth']):
        raise APIError(422, 'cameras', 'Send only cameras with matching RGB and depth calibration.')
    decoded = {k: value[k] for k in ('instruction', 'robot', 'step', 'eef_pose', 'joints', 'gripper')}
    decoded['images'], decoded['depth'] = {}, {}
    for name, depth in value['depth'].items():
        if not isinstance(name, str) or not 1 <= len(name) <= 64:
            raise APIError(422, 'cameras', 'Invalid camera name.')
        fields(depth, ('depth_m', 'intrinsics', 'base_from_camera'))
        decoded['images'][name] = decode_array(value['images'][name], 'rgb')
        decoded['depth'][name] = dict(depth_m=decode_array(depth['depth_m'], 'depth'),
            intrinsics=depth['intrinsics'], base_from_camera=depth['base_from_camera'])
        rgb_hw = decoded['images'][name].shape[:2]
        depth_hw = decoded['depth'][name]['depth_m'].shape
        grids = (rgb_hw, tuple(x * 2 for x in rgb_hw)) if value['robot'] == 'franka' else (rgb_hw,)
        if depth_hw not in grids:
            raise APIError(422, 'camera_grid', 'Preserve native grids: Franka depth is twice RGB size; WidowX grids match.')
    try:
        out = public_observation(decoded)
    except (ValueError, TypeError, KeyError, IndexError):
        raise APIError(422, 'observation', 'Public observation failed numerical or geometry validation.') from None
    if not generic and len(out['joints']) != 7:
        raise APIError(422, 'joints', 'Send seven native entries: Franka arm joints, or WidowX six arm joints plus finger position.')
    return out


def encode_observation(value):
    return dict(instruction=value['instruction'], robot=value['robot'], step=int(value['step']),
        eef_pose=np.asarray(value['eef_pose']).tolist(), joints=np.asarray(value['joints']).tolist(),
        gripper=float(value['gripper']), images={k: encode_array(v) for k, v in value['images'].items()},
        depth={k: dict(depth_m=encode_array(v['depth_m']), intrinsics=np.asarray(v['intrinsics']).tolist(),
            base_from_camera=np.asarray(v['base_from_camera']).tolist()) for k, v in value['depth'].items()})


def request_digest(body):
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def action(value):
    pose = np.asarray(value['eef_pose'], dtype=float)
    if pose.shape != (4, 4) or not np.isfinite(pose).all():
        raise ValueError('Invalid worker action pose.')
    grip = float(value['gripper'])
    if not math.isfinite(grip) or not 0 <= grip <= 1:
        raise ValueError('Invalid worker action gripper.')
    result = dict(type='joint_position' if 'joint_targets' in value else 'eef_pose',
        eef_pose=pose.tolist(), gripper=grip)
    if 'joint_targets' in value:
        q = np.asarray(value['joint_targets'], dtype=float)
        if q.shape != (7,) or not np.isfinite(q).all():
            raise ValueError('Invalid worker joint targets.')
        result['joint_targets'] = q.tolist()
    return result
