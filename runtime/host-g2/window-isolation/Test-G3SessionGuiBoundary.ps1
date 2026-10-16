# G3 source-only diagnostic: user-local Windows x64, no owner GUI content operations.
# OwnerWitness reads names/identity only. GuestProbe uses open/close capability probes.
# Guest clipboard is touched only if empty, or with explicit -ReplaceGuestClipboard.
[CmdletBinding()]
param(
    [ValidateSet('Validate','OwnerWitness','GuestProbe')][string]$Mode = 'Validate',
    [string]$OwnerWitnessBase64,
    [ValidatePattern('^[A-Fa-f0-9]{64}$')][string]$CapturedSHA256,
    [switch]$ReplaceGuestClipboard
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$guestSid = 'S-1-5-21-303538662-3368424508-2654684973-1009'
$ownerSid = 'S-1-5-21-303538662-3368424508-2654684973-1001'
$sourceHash = $CapturedSHA256
if (!$sourceHash) {
    if (!$PSCommandPath) { throw 'Captured execution requires the verified CapturedSHA256 parameter' }
    $sourceHash = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash
}
$sourceHash = $sourceHash.ToUpperInvariant()
if ('FortisG3SessionBoundary' -as [type]) { throw 'Use a fresh PowerShell process' }
$native = @'
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Security.Principal;
using System.Text;
using System.Threading;
public static class FortisG3SessionBoundary {
    [StructLayout(LayoutKind.Sequential)] struct US { public ushort Length, MaximumLength; public IntPtr Buffer; }
    [StructLayout(LayoutKind.Sequential)] struct OA { public int Length; public IntPtr Root, Name; public uint Attributes; public IntPtr Security, Qos; }
    [StructLayout(LayoutKind.Sequential)] struct FT { public uint Low, High; }
    [StructLayout(LayoutKind.Sequential)] struct POINT { public int X, Y; }
    [StructLayout(LayoutKind.Sequential)] struct MSG { public IntPtr Hwnd; public uint Message; public UIntPtr Wparam; public IntPtr Lparam; public uint Time; public POINT Point; public uint Private; }
    [DllImport("kernel32.dll", SetLastError=true)] static extern IntPtr OpenProcess(uint access, bool inherit, uint pid);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool CloseHandle(IntPtr h);
    [DllImport("kernel32.dll")] static extern void SetLastError(uint error);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool GetProcessTimes(IntPtr h, out FT created, out FT exited, out FT kernel, out FT user);
    [DllImport("kernel32.dll", SetLastError=true)] static extern uint GetProcessId(IntPtr h);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool ProcessIdToSessionId(uint pid, out uint session);
    [DllImport("advapi32.dll", SetLastError=true)] static extern bool OpenProcessToken(IntPtr p, uint access, out IntPtr token);
    [DllImport("advapi32.dll", SetLastError=true)] static extern bool GetTokenInformation(IntPtr token, int kind, IntPtr data, uint size, out uint needed);
    [DllImport("ntdll.dll")] static extern int NtQueryObject(IntPtr h, int kind, IntPtr data, uint size, out uint needed);
    // Undocumented ABI: phnt ntuser.h. No direct syscall numbers or fallback bypass.
    [DllImport("win32u.dll", SetLastError=true)] static extern IntPtr NtUserOpenWindowStation(ref OA attributes, uint access);
    [DllImport("win32u.dll", SetLastError=true)] static extern IntPtr NtUserOpenDesktop(ref OA attributes, uint flags, uint access);
    [DllImport("user32.dll", SetLastError=true)] static extern IntPtr GetProcessWindowStation();
    [DllImport("user32.dll")] static extern IntPtr GetThreadDesktop(uint tid);
    [DllImport("kernel32.dll")] static extern uint GetCurrentThreadId();
    [DllImport("user32.dll", SetLastError=true)] static extern bool CloseWindowStation(IntPtr h);
    [DllImport("user32.dll", SetLastError=true)] static extern bool CloseDesktop(IntPtr h);
    [DllImport("user32.dll", EntryPoint="GetUserObjectInformationW", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern bool UserName(IntPtr h, int kind, StringBuilder data, uint size, out uint needed);
    [DllImport("user32.dll", EntryPoint="CreateWindowExW", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern IntPtr CreateWindowEx(uint ex, string cls, string text, uint style, int x, int y, int width, int height, IntPtr parent, IntPtr menu, IntPtr instance, IntPtr parameter);
    [DllImport("user32.dll")] static extern bool ShowWindow(IntPtr h, int command);
    [DllImport("user32.dll")] static extern bool UpdateWindow(IntPtr h);
    [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
    [DllImport("user32.dll", SetLastError=true)] static extern bool DestroyWindow(IntPtr h);
    [DllImport("user32.dll")] static extern bool PeekMessage(out MSG message, IntPtr window, uint first, uint last, uint remove);
    [DllImport("user32.dll")] static extern bool TranslateMessage(ref MSG message);
    [DllImport("user32.dll")] static extern IntPtr DispatchMessage(ref MSG message);
    [DllImport("user32.dll", SetLastError=true)] static extern bool OpenClipboard(IntPtr h);
    [DllImport("user32.dll", SetLastError=true)] static extern bool CloseClipboard();
    [DllImport("user32.dll", SetLastError=true)] static extern bool EmptyClipboard();
    [DllImport("user32.dll", SetLastError=true)] static extern int CountClipboardFormats();
    [DllImport("user32.dll")] static extern IntPtr GetClipboardOwner();
    [DllImport("user32.dll", EntryPoint="RegisterClipboardFormatW", CharSet=CharSet.Unicode, SetLastError=true)] static extern uint RegisterClipboardFormat(string name);
    [DllImport("user32.dll", SetLastError=true)] static extern IntPtr SetClipboardData(uint format, IntPtr data);
    [DllImport("user32.dll", SetLastError=true)] static extern IntPtr GetClipboardData(uint format);
    [DllImport("user32.dll")] static extern bool IsClipboardFormatAvailable(uint format);
    [DllImport("kernel32.dll", SetLastError=true)] static extern IntPtr GlobalAlloc(uint flags, UIntPtr size);
    [DllImport("kernel32.dll", SetLastError=true)] static extern IntPtr GlobalLock(IntPtr h);
    [DllImport("kernel32.dll")] static extern bool GlobalUnlock(IntPtr h);
    [DllImport("kernel32.dll")] static extern UIntPtr GlobalSize(IntPtr h);
    [DllImport("kernel32.dll")] static extern IntPtr GlobalFree(IntPtr h);
    static void Check(bool ok, string stage) { if (!ok) throw new Win32Exception(Marshal.GetLastWin32Error(), stage); }
    public static string ObjectPath(IntPtr h) {
        uint needed; int first = NtQueryObject(h, 1, IntPtr.Zero, 0, out needed);
        if (needed < Marshal.SizeOf(typeof(US)) || needed > 65536) throw new InvalidOperationException("Object name length unavailable: " + first);
        IntPtr data = Marshal.AllocHGlobal((int)needed);
        try { int status = NtQueryObject(h, 1, data, needed, out needed); if (status < 0) throw new InvalidOperationException("NtQueryObject status " + status);
            US name = (US)Marshal.PtrToStructure(data, typeof(US));
            if (name.Buffer == IntPtr.Zero || name.Length == 0) throw new InvalidOperationException("Unnamed target");
            return Marshal.PtrToStringUni(name.Buffer, name.Length / 2);
        } finally { Marshal.FreeHGlobal(data); }
    }
    static string ShortName(IntPtr h) { uint n; var b = new StringBuilder(512); Check(UserName(h, 2, b, 1024, out n), "Object short name"); return b.ToString(); }
    public static Dictionary<string,object> OwnObjects() {
        IntPtr station = GetProcessWindowStation(), desktop = GetThreadDesktop(GetCurrentThreadId());
        Check(station != IntPtr.Zero && desktop != IntPtr.Zero, "Current objects");
        return new Dictionary<string,object> { {"Station",ShortName(station)}, {"Desktop",ShortName(desktop)}, {"StationPath",ObjectPath(station)}, {"DesktopPath",ObjectPath(desktop)} };
    }
    public static IntPtr HoldProcess(uint pid) { IntPtr h = OpenProcess(0x1000, false, pid); Check(h != IntPtr.Zero, "Open target QUERY_LIMITED_INFORMATION"); return h; }
    public static void ReleaseProcess(IntPtr h) { Check(CloseHandle(h), "Close process query handle"); }
    public static Dictionary<string,object> ProcessBasic(IntPtr h) {
        FT c, e, k, u; Check(GetProcessTimes(h, out c, out e, out k, out u), "Process creation time");
        if (e.Low != 0 || e.High != 0) throw new InvalidOperationException("Target process exited");
        uint pid = GetProcessId(h), session; Check(pid != 0, "Target PID"); Check(ProcessIdToSessionId(pid, out session), "Target session");
        return new Dictionary<string,object> { {"Session",session}, {"Created",(((ulong)c.High << 32) | c.Low).ToString()} };
    }
    public static Dictionary<string,object> ProcessMeta(IntPtr h) {
        FT c, e, k, u; Check(GetProcessTimes(h, out c, out e, out k, out u), "Process creation time");
        if (e.Low != 0 || e.High != 0) throw new InvalidOperationException("Target process exited");
        IntPtr token; Check(OpenProcessToken(h, 8, out token), "Target TOKEN_QUERY");
        try { uint n; GetTokenInformation(token, 1, IntPtr.Zero, 0, out n); if (n == 0 || n > 65536) throw new InvalidOperationException("Token user size");
            IntPtr b = Marshal.AllocHGlobal((int)n);
            try { Check(GetTokenInformation(token, 1, b, n, out n), "Token user"); string sid = new SecurityIdentifier(Marshal.ReadIntPtr(b)).Value;
                // TOKEN_SESSION_ID is a DWORD; separate buffer avoids assumptions about TOKEN_USER.
                IntPtr session = Marshal.AllocHGlobal(4);
                try { Check(GetTokenInformation(token, 12, session, 4, out n), "Token session");
                    return new Dictionary<string,object> { {"Sid",sid}, {"Session",Marshal.ReadInt32(session)}, {"Created",(((ulong)c.High << 32) | c.Low).ToString()} };
                } finally { Marshal.FreeHGlobal(session); }
            } finally { Marshal.FreeHGlobal(b); }
        } finally { Check(CloseHandle(token), "Close token query handle"); }
    }
    static IntPtr NativeHandle(string path, IntPtr root, bool desktop, uint access, out int error) {
        IntPtr text = Marshal.StringToHGlobalUni(path), name = IntPtr.Zero;
        try { US us = new US { Length=checked((ushort)(path.Length*2)), MaximumLength=checked((ushort)(path.Length*2+2)), Buffer=text };
            name = Marshal.AllocHGlobal(Marshal.SizeOf(typeof(US))); Marshal.StructureToPtr(us, name, false);
            OA oa = new OA { Length=Marshal.SizeOf(typeof(OA)), Root=root, Name=name, Attributes=0x40 };
            SetLastError(0);
            IntPtr h = desktop ? NtUserOpenDesktop(ref oa, 0, access) : NtUserOpenWindowStation(ref oa, access);
            error = h == IntPtr.Zero ? Marshal.GetLastWin32Error() : 0;
            return h;
        } finally { if (name != IntPtr.Zero) Marshal.FreeHGlobal(name); Marshal.FreeHGlobal(text); }
    }
    // A desktop name is bound to a verified station handle; never invent a full desktop path.
    public static Dictionary<string,object> NativeOpen(string stationPath, string desktopName, uint access) {
        bool desktop = !String.IsNullOrEmpty(desktopName); IntPtr root = IntPtr.Zero, h = IntPtr.Zero; int error;
        var r = new Dictionary<string,object> { {"Opened",false}, {"Win32",0}, {"Closed",true}, {"ResolvedPath",""}, {"MethodError",""},
            {"FailureStage",""}, {"RootOpened",false}, {"RootWin32",0}, {"RootClosed",true}, {"RootResolvedPath",""} };
        try {
            if (desktop) {
                // WINSTA_ENUMDESKTOPS only. Failure here is not an individual desktop-right denial.
                root = NativeHandle(stationPath, IntPtr.Zero, false, 1, out error);
                r["RootOpened"] = root != IntPtr.Zero; r["RootWin32"] = error;
                if (root == IntPtr.Zero) { r["FailureStage"]="STATION_ROOT"; r["Win32"]=error; return r; }
                try { r["RootResolvedPath"] = ObjectPath(root); }
                catch (Exception ex) { r["FailureStage"]="ROOT_METADATA"; r["MethodError"]=ex.GetType().Name; return r; }
                if (!String.Equals((string)r["RootResolvedPath"], stationPath, StringComparison.OrdinalIgnoreCase)) {
                    r["FailureStage"]="ROOT_METADATA"; r["MethodError"]="RootNameMismatch"; return r;
                }
            }
            h = NativeHandle(desktop ? desktopName : stationPath, root, desktop, access, out error);
            r["Opened"] = h != IntPtr.Zero; r["Win32"] = error;
            if (h == IntPtr.Zero) r["FailureStage"]="TARGET";
            else { try { r["ResolvedPath"] = ObjectPath(h); } catch (Exception ex) { r["MethodError"] = ex.GetType().Name; } }
        } catch (EntryPointNotFoundException) { r["MethodError"] = "NativeEntryPointUnavailable"; }
          catch (DllNotFoundException) { r["MethodError"] = "NativeLibraryUnavailable"; }
        finally {
            if (h != IntPtr.Zero) r["Closed"] = desktop ? CloseDesktop(h) : CloseWindowStation(h);
            if (root != IntPtr.Zero) r["RootClosed"] = CloseWindowStation(root);
        }
        return r;
    }
    public static Dictionary<string,object> ProcessOpen(uint pid, uint access) {
        IntPtr h = OpenProcess(access, false, pid); int e = Marshal.GetLastWin32Error();
        return new Dictionary<string,object> { {"Opened",h != IntPtr.Zero}, {"Win32",h == IntPtr.Zero ? e : 0}, {"Closed",h == IntPtr.Zero || CloseHandle(h)} };
    }
    static bool ClipboardLock(IntPtr h) { for (int i=0; i<5; i++) { if (OpenClipboard(h)) return true; Thread.Sleep(50); } return false; }
    public static Dictionary<string,object> GuestGui(bool replace) {
        var r = new Dictionary<string,object> { {"WindowCreated",false}, {"WindowVisible",false}, {"WindowDestroyed",false}, {"Clipboard","NOT_RUN"}, {"ClipboardCleanup","NOT_NEEDED"} };
        IntPtr window = IntPtr.Zero, allocation = IntPtr.Zero; uint format = 0; bool ownsData = false;
        string expectedMarker = "Fortis-G3-" + Guid.NewGuid().ToString("N");
        try {
            window = CreateWindowEx(0x08000000, "STATIC", "Fortis G3: own guest test window", 0x00cf0000, 40, 40, 440, 110, IntPtr.Zero, IntPtr.Zero, IntPtr.Zero, IntPtr.Zero);
            Check(window != IntPtr.Zero, "Own guest window"); uint pid; GetWindowThreadProcessId(window, out pid);
            if (pid != (uint)Process.GetCurrentProcess().Id) throw new InvalidOperationException("Unexpected window PID");
            r["WindowCreated"] = true; ShowWindow(window, 4); UpdateWindow(window); r["WindowVisible"] = IsWindowVisible(window);
            for (int i=0; i<5; i++) { MSG msg; while (PeekMessage(out msg, window, 0, 0, 1)) { TranslateMessage(ref msg); DispatchMessage(ref msg); } Thread.Sleep(50); }
            Check(ClipboardLock(window), "Open own guest clipboard");
            try {
                SetLastError(0); int formats = CountClipboardFormats(); int countError = Marshal.GetLastWin32Error();
                if (formats == 0 && countError != 0) throw new Win32Exception(countError, "Clipboard format count");
                if (formats != 0 && !replace) { r["Clipboard"] = "SKIPPED_NONEMPTY"; return r; }
                format = RegisterClipboardFormat("Fortis.G3.Synthetic." + Guid.NewGuid().ToString("N")); Check(format != 0, "Own format");
                byte[] marker = Encoding.Unicode.GetBytes(expectedMarker + "\0");
                allocation = GlobalAlloc(0x42, (UIntPtr)(uint)marker.Length); Check(allocation != IntPtr.Zero, "Own marker allocation");
                IntPtr b = GlobalLock(allocation); Check(b != IntPtr.Zero, "Own marker lock");
                try { Marshal.Copy(marker, 0, b, marker.Length); } finally { GlobalUnlock(allocation); }
                Check(EmptyClipboard(), "Empty own guest clipboard");
                Check(SetClipboardData(format, allocation) != IntPtr.Zero, "Set own marker"); allocation = IntPtr.Zero; ownsData = true;
            } finally { Check(CloseClipboard(), "Close own guest clipboard after write"); }
            Check(ClipboardLock(window), "Reopen own guest clipboard");
            try {
                if (GetClipboardOwner() != window || !IsClipboardFormatAvailable(format)) throw new InvalidOperationException("Own marker changed before read");
                IntPtr data = GetClipboardData(format); Check(data != IntPtr.Zero, "Read only own custom format");
                ulong size = GlobalSize(data).ToUInt64(); if (size == 0 || size > 256) throw new InvalidOperationException("Unexpected marker size");
                IntPtr b = GlobalLock(data); Check(b != IntPtr.Zero, "Own roundtrip lock");
                try { string marker = Marshal.PtrToStringUni(b, (int)size / 2).TrimEnd('\0');
                    // Only our registered format is read; compare the exact per-run marker.
                    r["Clipboard"] = marker == expectedMarker ? "ROUNDTRIP_EXACT_MARKER" : "MISMATCH";
                } finally { GlobalUnlock(data); }
            } finally { Check(CloseClipboard(), "Close own guest clipboard after read"); }
        } finally {
            if (allocation != IntPtr.Zero) GlobalFree(allocation);
            if (ownsData) {
                if (!ClipboardLock(window)) r["ClipboardCleanup"] = "FAILED_BUSY";
                else { try { if (GetClipboardOwner() == window && IsClipboardFormatAvailable(format)) { r["ClipboardCleanup"] = EmptyClipboard() ? "EMPTIED_OWN_MARKER" : "FAILED_EMPTY"; } else r["ClipboardCleanup"] = "CHANGED_LEFT_UNTOUCHED"; }
                    finally { if (!CloseClipboard()) r["ClipboardCleanup"] = "FAILED_CLOSE"; } }
            }
            if (window != IntPtr.Zero) r["WindowDestroyed"] = DestroyWindow(window);
        }
        return r;
    }
}
'@
Add-Type -TypeDefinition $native -ErrorAction Stop
if ($Mode -eq 'Validate') {
    [pscustomobject]@{ Mode=$Mode; SourceSHA256=$sourceHash; CSharpCompiled=$true; NativeCallsExecuted=$false } | ConvertTo-Json -Compress
    return
}
if ($env:OS -ne 'Windows_NT' -or ![Environment]::Is64BitProcess) { throw 'Windows x64 PowerShell required' }
$id = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($id)
$admin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
$session = [Diagnostics.Process]::GetCurrentProcess().SessionId
if ($admin) { throw 'Use an ordinary, non-elevated PowerShell' }
if ($Mode -eq 'GuestProbe' -and ($id.User.Value -ne $guestSid -or @($id.Groups | Where-Object Value -eq 'S-1-5-32-544').Count -ne 0)) { throw 'Exact guest SID1009 without Administrators membership required' }
if ($Mode -eq 'OwnerWitness' -and $id.User.Value -ne $ownerSid) { throw 'Exact owner SID1001 required for metadata witness' }
$objects = [FortisG3SessionBoundary]::OwnObjects()
$stationPath = '\Sessions\' + $session + '\Windows\WindowStations\WinSta0'
$desktopName = 'Default'
$desktopObjectName = $objects.DesktopPath
if ($objects.Station -ine 'WinSta0' -or $objects.Desktop -ine $desktopName -or $objects.StationPath -ine $stationPath -or $desktopObjectName -notin @('\Default',($stationPath + '\Default'))) { throw 'Expected own WinSta0 station and station-relative Default desktop not established' }
$heldSelf = [FortisG3SessionBoundary]::HoldProcess([uint32]$PID)
try { $self = [FortisG3SessionBoundary]::ProcessMeta($heldSelf) } finally { [FortisG3SessionBoundary]::ReleaseProcess($heldSelf) }
if ($self.Sid -ne $id.User.Value -or $self.Session -ne $session) { throw 'Effective identity differs from own process token/session' }
if ($Mode -eq 'OwnerWitness') {
    $witness = [ordered]@{ Schema=2; CreatedUtc=[DateTime]::UtcNow.ToString('o'); CreatedUnixSeconds=[DateTimeOffset]::UtcNow.ToUnixTimeSeconds(); SourceSHA256=$sourceHash; Sid=$id.User.Value; Session=$session; Pid=$PID; ProcessCreated=$self.Created; StationPath=$stationPath; DesktopName=$desktopName; DesktopObjectName=$desktopObjectName }
    $json = $witness | ConvertTo-Json -Compress
    [pscustomobject]@{ Mode=$Mode; Witness=$witness; OwnerWitnessBase64=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($json)); KeepThisPowerShellOpen=$true; GuiContentRead=$false } | ConvertTo-Json -Depth 5
    return
}
if (!$OwnerWitnessBase64 -or $OwnerWitnessBase64.Length -gt 8192) { throw 'Paste the selected owner metadata witness (at most 8192 Base64 characters)' }
$w = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($OwnerWitnessBase64)) | ConvertFrom-Json
$age = ([DateTimeOffset]::UtcNow.ToUnixTimeSeconds() - [long]$w.CreatedUnixSeconds) / 60.0
if ($w.Schema -ne 2 -or $w.SourceSHA256 -ne $sourceHash -or $w.Sid -ne $ownerSid -or $w.Session -eq $session -or $w.Session -le 0 -or $age -lt 0 -or $age -gt 30) { throw 'Wrong, stale, or same-session owner witness; no DENY verdict' }
$ownerStation = '\Sessions\' + [int]$w.Session + '\Windows\WindowStations\WinSta0'
if ($w.StationPath -ine $ownerStation -or $w.DesktopName -ine 'Default' -or $w.DesktopObjectName -notin @('\Default',($ownerStation + '\Default'))) { throw 'Invalid owner station/relative desktop witness' }
$heldOwner = [FortisG3SessionBoundary]::HoldProcess([uint32]$w.Pid)
try {
    $target = [FortisG3SessionBoundary]::ProcessBasic($heldOwner)
    if ($target.Session -ne $w.Session -or $target.Created -ne $w.ProcessCreated) { throw 'Owner witness PID/session/creation mismatch; no DENY verdict' }
    $rows = @()
    $cases = @(
        @('Station','ACCESSCLIPBOARD',4), @('Station','READSCREEN',512), @('Station','WRITE_DAC',262144), @('Station','WRITE_OWNER',524288),
        @('Desktop','READOBJECTS',1), @('Desktop','HOOKCONTROL',8), @('Desktop','WRITEOBJECTS',128),
        @('Desktop','SWITCHDESKTOP',256), @('Desktop','WRITE_DAC_WITH_READ_WRITE',262273), @('Desktop','WRITE_OWNER_WITH_READ_WRITE',524417)
    )
    foreach ($case in $cases) {
        $isDesktop = $case[0] -eq 'Desktop'; $name = $null; $ownObjectName = $stationPath
        $missingStation = $stationPath; $missingName = $null
        if ($isDesktop) { $name=$desktopName; $ownObjectName=$desktopObjectName; $missingName=$desktopName + '-missing-' + [Guid]::NewGuid().ToString('N') }
        else { $missingStation += '-missing-' + [Guid]::NewGuid().ToString('N') }
        $positive = [FortisG3SessionBoundary]::NativeOpen($stationPath, $name, [uint32]$case[2])
        $missing = [FortisG3SessionBoundary]::NativeOpen($missingStation, $missingName, [uint32]$case[2])
        $control = $positive.Opened -and $positive.Closed -and $positive.RootClosed -and $positive.ResolvedPath -ieq $ownObjectName -and !$positive.MethodError -and !$missing.Opened -and $missing.Closed -and $missing.RootClosed -and !$missing.MethodError -and $missing.FailureStage -eq 'TARGET' -and $missing.Win32 -in @(2,3)
        if ($isDesktop) { $control = $control -and $positive.RootOpened -and $positive.RootResolvedPath -ieq $stationPath -and $missing.RootOpened -and $missing.RootResolvedPath -ieq $stationPath }
        $negative = $null; $verdict = 'INCONCLUSIVE_METHOD_CONTROL'
        if ($control) {
            $negative = [FortisG3SessionBoundary]::NativeOpen($ownerStation, $name, [uint32]$case[2])
            $verdict = 'INCONCLUSIVE_NATIVE_ERROR'
            if ($negative.Opened) { $verdict='OWNER_HANDLE_OPENED_REVIEW' }
            elseif (!$negative.MethodError -and $negative.Win32 -eq 5) {
                if ($negative.FailureStage -eq 'STATION_ROOT') { $verdict='DENIED_STATION_ROOT_DESKTOP_NOT_TESTED' }
                elseif ($negative.FailureStage -eq 'TARGET') { $verdict='DENIED_OPEN_WITNESS_BACKED' }
            }
            if (!$negative.Closed -or !$negative.RootClosed) { $verdict='CLEANUP_FAILED' }
        }
        $rows += [pscustomobject]@{ Object=$case[0]; Right=$case[1]; Mask=$case[2]; Verdict=$verdict; Self=$positive; Missing=$missing; Owner=$negative }
    }
    $processRows = @()
    foreach ($case in @(@('DUP_HANDLE',64),@('CREATE_THREAD',2),@('VM_OPERATION',8),@('VM_READ',16),@('VM_WRITE',32))) {
        $positive=[FortisG3SessionBoundary]::ProcessOpen([uint32]$PID,[uint32]$case[1]); $negative=[FortisG3SessionBoundary]::ProcessOpen([uint32]$w.Pid,[uint32]$case[1])
        $verdict='INCONCLUSIVE_PROCESS_CONTROL'
        if ($positive.Opened -and $positive.Closed -and $negative.Closed) {
            if ($negative.Opened) { $verdict='OWNER_PROCESS_HANDLE_OPENED_REVIEW' }
            elseif ($negative.Win32 -eq 5) { $verdict='DENIED_OPEN_VALIDATED_PID' }
        }
        $processRows += [pscustomobject]@{ Right=$case[0]; Mask=$case[1]; Verdict=$verdict; Self=$positive; Owner=$negative }
    }
    $gui=[FortisG3SessionBoundary]::GuestGui([bool]$ReplaceGuestClipboard)
    $after=[FortisG3SessionBoundary]::ProcessBasic($heldOwner)
    if ($after.Created -ne $target.Created -or $after.Session -ne $target.Session) { throw 'Owner witness changed during probes; discard negative verdicts' }
    [pscustomobject]@{
        Mode=$Mode; SourceSHA256=$sourceHash; GuestSid=$id.User.Value; GuestSession=$session; Admin=$admin
        OwnerSession=$w.Session; WitnessAgeMinutes=[Math]::Round($age,2); GuestObjects=$objects
        OwnerSidSource='OPERATOR_WITNESS_VERIFIED_IN_OWNER'; OwnerTokenQueriedFromGuest=$false
        NativeObjectProbes=$rows; OwnerWitnessProcessProbes=$processRows; GuestGui=$gui
        Overall='SCOPED_DIAGNOSTIC_ONLY_G3_PENDING'; FinalMcpChainChecked=$false; ExistingHandlesInventoried=$false; ClipboardBridgesChecked=$false
        OwnerContentReads=0; AclWrites=0; StationDesktopSwitches=0; InputInjection=0; Captures=0
    } | ConvertTo-Json -Depth 8
} finally { [FortisG3SessionBoundary]::ReleaseProcess($heldOwner) }
