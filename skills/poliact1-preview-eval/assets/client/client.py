"""Simple HTTP observations-to-actions client with safe sequence retries."""
import http.client
import json
import secrets
import time
import ssl
import urllib.request
import urllib.error
from pathlib import Path
from urllib.parse import urlsplit


class RemoteError(RuntimeError):
    def __init__(self,message,*,status=None,code=None,retry_after=2):
        super().__init__(message)
        self.status,self.code,self.retry_after=status,code,retry_after


class Client:
    def __init__(self,url,token='',ca_file=None,*,request_timeout=45,action_timeout=None):
        parts=urlsplit(url)
        if parts.scheme not in ('http','https') or not parts.hostname or parts.query or parts.fragment or parts.username or parts.password:
            raise ValueError('Use an HTTP(S) base URL without credentials or query.')
        self.url,self.token=url.rstrip('/'),token.strip()
        if ca_file is None and parts.scheme=='https' and parts.port==18443 and parts.hostname in ('115.190.169.226','192.168.0.179','127.0.0.1','localhost','54.248.203.96'):
            bundled=Path(__file__).resolve().parent/'server-ca.crt'
            if bundled.is_file():ca_file=bundled
        self.context=ssl.create_default_context(cafile=str(ca_file) if ca_file else None)
        self.timeout,self.action_timeout=request_timeout,action_timeout
        self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),
            urllib.request.HTTPSHandler(context=self.context))

    def request(self,method,path,body=None,*,idempotency=None):
        raw=None if body is None else json.dumps(body,separators=(',',':'),allow_nan=False).encode()
        headers={'Content-Type':'application/json'}
        if self.token:headers['X-API-Key']=self.token
        if idempotency:headers['Idempotency-Key']=idempotency
        req=urllib.request.Request(self.url+path,data=raw,method=method,headers=headers)
        try:
            with self.opener.open(req,timeout=self.timeout) as response:
                return response.status,json.load(response)
        except urllib.error.HTTPError as error:
            try:detail=json.load(error).get('error',{})
            except (ValueError,AttributeError):detail={}
            if not isinstance(detail,dict):
                detail={'code':'gateway_error','message':str(detail)}
            try:delay=max(1,min(86400,int(error.headers.get('Retry-After','2'))))
            except ValueError:delay=2
            raise RemoteError(f"HTTP {error.code}: {detail.get('code','request_failed')}: {detail.get('message','')}",
                status=error.code,code=detail.get('code'),retry_after=delay) from None

    def _deadline(self):
        return None if self.action_timeout is None else time.monotonic()+self.action_timeout

    def _retry(self,method,path,body=None,*,idempotency=None,deadline=None):
        while True:
            if deadline is not None and time.monotonic()>=deadline:
                raise RemoteError('Caller-selected wait deadline reached; do not silently rerun the episode.')
            try:return self.request(method,path,body,idempotency=idempotency)
            except RemoteError as error:
                if error.status not in (408,429,500,502,503,504):raise
                delay=error.retry_after
            except (urllib.error.URLError,TimeoutError,ConnectionError,http.client.HTTPException):
                delay=2
            if deadline is not None:delay=min(delay,max(0,deadline-time.monotonic()))
            time.sleep(delay)

    def register(self,label='evaluation'):
        """Register once, persist privately, reuse the same key for all episodes."""
        return self.request('POST','/v1/keys',dict(accept_terms=True,label=label))[1]

    def create(self,*,instruction,robot,max_steps,idempotency_key=None):
        return self._retry('POST','/v1/sessions',dict(instruction=instruction,robot=robot,
            max_steps=max_steps),idempotency=idempotency_key or secrets.token_hex(24),
            deadline=self._deadline())[1]

    def step(self,session_id,sequence,observation):
        """Wait without a total deadline by default. Never execute a duplicate action."""
        deadline=self._deadline()
        status,value=self._retry('POST',f'/v1/sessions/{session_id}/step',
            dict(sequence=sequence,observation=observation,wait_s=25),deadline=deadline)
        while status==202:
            status,value=self._retry('GET',f'/v1/sessions/{session_id}/actions?sequence={sequence}&wait_s=25',deadline=deadline)
        if value.get('status')=='error':raise RemoteError(value.get('error_code','policy_worker_failed'))
        return value

    def end(self,session_id,reason='native_episode_over'):
        # Ending is idempotent; bounded cleanup does not mask a simulator exception.
        return self._retry('POST',f'/v1/sessions/{session_id}/end',dict(reason=reason),
            deadline=time.monotonic()+90)[1]
