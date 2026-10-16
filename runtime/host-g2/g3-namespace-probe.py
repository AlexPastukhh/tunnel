import ctypes, json, os
from ctypes import wintypes as w
adv=ctypes.WinDLL("advapi32",use_last_error=True)
kernel=ctypes.WinDLL("kernel32",use_last_error=True)
kernel.GetCurrentProcess.restype=w.HANDLE
adv.OpenProcessToken.argtypes=[w.HANDLE,w.DWORD,ctypes.POINTER(w.HANDLE)]
adv.GetTokenInformation.argtypes=[w.HANDLE,ctypes.c_int,ctypes.c_void_p,w.DWORD,ctypes.POINTER(w.DWORD)]
adv.ConvertSidToStringSidW.argtypes=[ctypes.c_void_p,ctypes.POINTER(w.LPWSTR)]
kernel.LocalFree.argtypes=[ctypes.c_void_p]
kernel.CloseHandle.argtypes=[w.HANDLE]
token=w.HANDLE()
if not adv.OpenProcessToken(kernel.GetCurrentProcess(),8,ctypes.byref(token)):
    raise ctypes.WinError(ctypes.get_last_error())
try:
    size=w.DWORD()
    adv.GetTokenInformation(token,1,None,0,ctypes.byref(size))
    buf=ctypes.create_string_buffer(size.value)
    if not adv.GetTokenInformation(token,1,buf,size.value,ctypes.byref(size)):
        raise ctypes.WinError(ctypes.get_last_error())
    sidptr=ctypes.cast(buf,ctypes.POINTER(ctypes.c_void_p))[0]
    sidstr=w.LPWSTR()
    if not adv.ConvertSidToStringSidW(sidptr,ctypes.byref(sidstr)):
        raise ctypes.WinError(ctypes.get_last_error())
    try: sid=sidstr.value
    finally: kernel.LocalFree(ctypes.cast(sidstr,ctypes.c_void_p))
    elevation=w.DWORD()
    if not adv.GetTokenInformation(token,20,ctypes.byref(elevation),ctypes.sizeof(elevation),ctypes.byref(size)):
        raise ctypes.WinError(ctypes.get_last_error())
finally: kernel.CloseHandle(token)
if sid!="S-1-5-21-303538662-3368424508-2654684973-1009" or elevation.value:
    raise RuntimeError("Wrong token")
root=r"C:\Users\Public\Documents\FortisHostG1Probe"
extended=chr(92)*2+"?"+chr(92)
unc=r"\\localhost\C$\Users\Public\Documents\FortisHostG1Probe"
results=[]
for namespace,prefix in [("extended",extended+root),("local_admin_share",unc)]:
    for kind in ["RW","RO","DENY"]:
        path=prefix+chr(92)+kind+chr(92)+"marker.txt"
        try:
            with open(path,"rb") as f: length=len(f.read())
            row={"namespace":namespace,"kind":kind,"read":"ALLOW","length":length}
        except OSError as e:
            row={"namespace":namespace,"kind":kind,"read":"DENY" if isinstance(e,PermissionError) or e.errno==13 or e.winerror in (5,1326) else "BLOCKED","winerror":e.winerror,"errno":e.errno,"errorType":type(e).__name__}
        results.append(row)
print(json.dumps({"pid":os.getpid(),"sid":sid,"elevated":bool(elevation.value),"readOnly":True,"results":results},indent=2))
