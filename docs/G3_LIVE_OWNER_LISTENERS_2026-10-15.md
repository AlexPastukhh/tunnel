# G3 — Owner session live tunnel listener inventory, 2026-10-15

**ACTUAL OWNER LISTENER PREVIEW PASS + GUEST UNAUTHENTICATED GET HTTP 200 ON BOTH OWNER PORTS; ADMIN SURFACE GATE FAIL / G3 BLOCKED.** The GET proof is narrowly for `/api/log-level` and does not establish successful PUT/POST or mutation.

## Evidence

User executed SHA256-pinned `runtime/host-g2/Preview-G3TunnelListeners.ps1` (`900196F0B19A83968F00DF91A9180DAB5F668433011799E0ED5DD690F223C0BE`) in ordinary owner PowerShell. Source returned:

```json
{"Kind":"G3_TUNNEL_LISTENER_PREVIEW","Schema":1,"ActorSid":"S-1-5-21-303538662-3368424508-2654684973-1001","ActorSession":2,"SnapshotUtc":"2026-10-14T20:04:59.9309689Z","Scope":"tunnel-client.exe and tunnel-client-runtime.exe only; no network requests","ProcessCount":2,"Processes":[{"ProcessId":31064,"Name":"tunnel-client.exe","SessionId":2,"IdentityClass":"OWNER","OwnerLookup":"OK","Listening":[{"LocalAddress":"127.0.0.1","LocalPort":52632}]},{"ProcessId":28376,"Name":"tunnel-client.exe","SessionId":2,"IdentityClass":"OWNER","OwnerLookup":"OK","Listening":[{"LocalAddress":"127.0.0.1","LocalPort":8080}]}],"AclWrites":0,"ProcessStarts":0,"ProcessStops":0,"HttpRequests":0,"SecretValuesRead":false}
```

Owner SID1001, Session 2, two tunnel-client.exe listeners; no `tunnel-client-runtime.exe` or SID1009 G2 tunnel-client processes **observed in this process-name-scoped inventory**. No evidence of absence of *all* guest processes. This inventory does **not** identify which specific owner tunnel profile corresponds to PID 31064 vs 28376 and does not prove any HTTP route currently reachable from guest. Ports may change on restart.

Historical G2 on 2026-10-13 got unauthenticated `GET /api/log-level` HTTP 200 against owner tunnel listeners; `OPTIONS` advertised GET,PUT. No mutation call was made. The present snapshot gives two new targets to verify GET from non-admin SID1009 in Windows Session 3; do not assert GET remains reachable until tested.

## Actual non-admin guest Session 3 localhost GET result — FAIL for API isolation

The user locally ran the **status-only** GET probe as SID1009, non-admin, Session 3, without credentials or response body reads. Raw synthetic output:

```json
{"Sid":"S-1-5-21-303538662-3368424508-2654684973-1009","Session":3,"Admin":false,"Method":"GET","CredentialsSent":false,"BodyRead":false,"Results":[{"Port":52632,"HttpStatus":200,"NetworkError":null},{"Port":8080,"HttpStatus":200,"NetworkError":null}]}
```

Both owner-owned `tunnel-client.exe` listener ports observed earlier in Session2 returned HTTP **200** to guest on `GET /api/log-level` (127.0.0.1, no auth). This is an **actual cross-Windows-session reachability** result: OS Session3 does not itself restrict TCP loopback endpoints bound by the owner. It fails the desired **owner admin HTTP route inaccessible to G2** acceptance property for this tested path.

**Proven:** non-admin SID1009 was permitted to issue unauthenticated HTTP GET on the two endpoints. **Not proven:** response content visibility (not read), settings mutation, successful admin PUT/POST, mapping of either PID to specific HOST/Repo profile, or other endpoint permissions. Do NOT test PUT/POST on live owner profiles, expose response bodies/keys or change firewall/protection settings.

Preferred bounded mitigation hypothesis, **not yet applied**: migrate owner native HOST/Repo run-executables to previously isolated-tested official `tunnel-client-runtime.exe` flavor with absent admin/UI routes, while retaining full client for doctor/init. The repo-pinned migration candidates may break other behavior and both tunnels carry established chats, so require a separate compatibility review and explicit owner authorization for each production process restart/launcher change. Do not silently apply the earlier three-launcher migration bundle.

## Historical guest-local GET-header-only test instructions (already run; do NOT repeat)

User must manually switch to existing guest Session3 without logging owner out and use ordinary non-admin PowerShell. The code below contacts **only** HTTP 127.0.0.1 ports 52632 and 8080 with `GET /api/log-level`, no Authorization or Cookie, no default Windows credentials, no redirects and no proxy; reports **status only**, not body or headers. It does not send PUT, POST, PATCH or DELETE. If a request is refused or endpoint changed, that is evidence; do not retry or scan ports. There is a bounded two-second timeout per request. The result is a diagnostic only, not a G3 denial acceptance.

```powershell
& {
  $ErrorActionPreference='Stop'
  $sid='S-1-5-21-303538662-3368424508-2654684973-1009'
  $id=[Security.Principal.WindowsIdentity]::GetCurrent()
  $session=[Diagnostics.Process]::GetCurrentProcess().SessionId
  $admin=(New-Object Security.Principal.WindowsPrincipal($id)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  if($id.User.Value -ne $sid -or $session -ne 3 -or $admin){throw 'Guest SID1009/Session3/non-admin required; no HTTP sent'}
  $result=@(foreach($port in @(52632,8080)){
    $response=$null; $status=$null; $netError=$null
    try{
      $req=[System.Net.HttpWebRequest][System.Net.WebRequest]::Create(('http://127.0.0.1:'+ $port +'/api/log-level'))
      $req.Method='GET'
      $req.Timeout=2000
      $req.ReadWriteTimeout=2000
      $req.AllowAutoRedirect=$false
      $req.UseDefaultCredentials=$false
      $req.Credentials=$null
      $req.Proxy=$null
      $req.KeepAlive=$false
      $response=$req.GetResponse()
      $status=[int]([System.Net.HttpWebResponse]$response).StatusCode
    }catch [System.Net.WebException]{
      $netError=[string]$_.Exception.Status
      if($_.Exception.Response){
        $response=$_.Exception.Response
        $status=[int]([System.Net.HttpWebResponse]$response).StatusCode
      }
    }finally{
      if($null -ne $response){$response.Close()}
    }
    [pscustomobject]@{Port=$port;HttpStatus=$status;NetworkError=$netError}
  })
  [pscustomobject]@{Sid=$id.User.Value;Session=$session;Admin=$admin;Method='GET';Path='/api/log-level';CredentialsSent=$false;BodyRead=$false;Results=$result} |
    ConvertTo-Json -Compress -Depth 4
}
```

**Stop on Kaspersky warning** and do not add AV exceptions. The test intentionally does not read HTTP response content or any private data, and does not modify configuration. If one response is 200, the historical exposure is still present on that port. If both are 404/403/401, this supports narrower refusal *only for the tested path at this time*, not all admin APIs. If connection fails, distinguish port drift/process absence from authorization denial.

**No Windows execution by assistant, process restart, ACL/task/service/network config change or Git commit/push.** The guest HTTP test remains PENDING.
