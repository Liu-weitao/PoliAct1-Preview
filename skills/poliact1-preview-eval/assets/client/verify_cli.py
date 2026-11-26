"""Portable evaluator check: one URL and one interactively supplied API key."""
import argparse
import getpass
import json
import os
from pathlib import Path

from client import Client
from access import client_settings, DEFAULT_URL


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--url')
    p.add_argument('--access-file',type=Path)
    p.add_argument('--observation',type=Path,help='Optional encoded RGB-D/end-effector observation JSON for one action smoke')
    p.add_argument('--max-steps',type=int)
    args=p.parse_args()
    if args.access_file or os.environ.get('POLIACT1_PREVIEW_ACCESS_FILE') or os.environ.get('POLIACT1_PREVIEW_API_KEY'):
        url,key=client_settings(args.access_file,args.url)
    else:
        url,key=args.url or DEFAULT_URL,getpass.getpass('PoliAct1-Preview API key: ')
    client=Client(url,key)
    info = client.request('GET','/v1/info')[1]
    print(json.dumps(dict(connected=True, system=info.get('system'),
                          model=info.get('model'), url=client.url),
                     ensure_ascii=False, indent=2))
    if args.observation:
        if not args.max_steps:p.error('Observation smoke requires --max-steps.')
        obs=json.loads(args.observation.read_text());session=None
        try:
            session=client.create(instruction=obs['instruction'],robot=obs['robot'],max_steps=args.max_steps)['session_id']
            print(json.dumps(client.step(session,0,obs),ensure_ascii=False,indent=2))
        finally:
            if session:client.end(session,'client_closed')


if __name__=='__main__':main()
