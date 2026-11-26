"""Self-service evaluation access: no approval, account or provider key required."""
import argparse
import json
import os
from pathlib import Path

from client import Client
from access import DEFAULT_URL


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--url',default=DEFAULT_URL,help='API base URL, including the /ladder prefix')
    p.add_argument('--access-file',type=Path,required=True,help='New private file on your own machine; never put it in the shared client package')
    p.add_argument('--accept-terms',action='store_true',help='Accept the uniform published free evaluation limits')
    args=p.parse_args()
    client=Client(args.url)
    policy=client.request('GET','/v1/access-policy')[1]
    print(json.dumps(policy,ensure_ascii=False,indent=2))
    if not args.accept_terms:p.error('Review the policy above, then add --accept-terms to register.')
    # Reserve the path before issuing a key, avoiding accidental overwrite or symlink following.
    fd=os.open(args.access_file,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        issued=client.register()
        with os.fdopen(fd,'w')as stream:
            fd=None
            os.fchmod(stream.fileno(),0o600)
            json.dump(dict(url=client.url,api_key=issued['api_key'],key_id=issued['key_id'],expires_at=issued['expires_at']),stream,indent=2)
            stream.write('\n')
    except BaseException:
        if fd is not None:os.close(fd)
        args.access_file.unlink(missing_ok=True)
        raise
    print(json.dumps(dict(access_file=str(args.access_file.resolve()),key_id=issued['key_id'],
        expires_at=issued['expires_at'],api_key_printed=False,human_approval_required=False)))


if __name__=='__main__':main()
