"""Client-owned access only; no deployment-owner or model-provider credential."""
import json
import os
from pathlib import Path

DEFAULT_URL = 'https://uat-open.qj-robots.com/ladder'

def client_settings(access_file=None,url=None):
    selected=access_file or os.environ.get('POLIACT1_PREVIEW_ACCESS_FILE')
    saved=json.loads(Path(selected).read_text()) if selected else {}
    key=os.environ.get('POLIACT1_PREVIEW_API_KEY') or saved.get('api_key','')
    base=url or os.environ.get('POLIACT1_PREVIEW_URL') or saved.get('url','') or DEFAULT_URL
    if not key or not base:
        raise ValueError('Supply URL + API key, or run register_cli.py once and set POLIACT1_PREVIEW_ACCESS_FILE.')
    if not key.isascii() or len(key)>4096 or any(c.isspace() for c in key):
        raise ValueError('Invalid evaluation API key format.')
    return base,key


def verifier_token():
    return client_settings()[1]
