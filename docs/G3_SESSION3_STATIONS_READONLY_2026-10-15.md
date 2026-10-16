# G3 — actual SID1009 Session 3 window-station metadata, 2026-10-15

**Актуальная роль:** evidence names-only inspection. Private station — условный fallback, собственные guest GUI/clipboard разрешены; owner boundary ещё требует приёмки. Разрешения и оставшиеся проверки поддерживаются [в плане](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md).

**Actual guest-local metadata PASS; independent private G2 window station NOT created; G3 BLOCKED.** No Windows ACL, process, clipboard or desktop modification.

## User-observed native result

Executed pinned `runtime/host-g2/window-isolation/Inspect-G3GuestStations.ps1` SHA256 `941FED61BEB08A9370AEDFF8D4E05511AC4A896B9BCAD293312F2C7792BEB4E4` from non-elevated `FortisHostG1` PowerShell in client Session 3. Local file SHA check passed. Report:

```json
{"Sid":"S-1-5-21-303538662-3368424508-2654684973-1009","Session":3,"Admin":false,"CurrentStationName":"WinSta0","CurrentStationVisible":true,"EnumerationAllowed":true,"EnumerationWin32":0,"AccessibleStationNames":["WinSta0","Service-0x0-218d7932$"],"Creates":0,"AclWrites":0,"DesktopReads":0,"OwnerSessionTouched":false}
```

This proves the guest calling process is on **its own Session 3 interactive `WinSta0`**, not an additional private station. Enumeration succeeded and reported a second visible *name* `Service-0x0-218d7932$`. This does **not** prove SID1009 owns that object, has DACL rights on it, can safely open it, or may assign G2 to it. It is **not** an approved private-G2 target. No existing station opened or switched; no desktop/window enumeration and no clipboard or screen contents read.

The earlier `CreateWindowStation(null,CWF_CREATE_ONLY=1,...)` failed Win32 183; that is consistent with the logon-derived name already existing, not evidence of an ACL denial. Specifying `FortisG3-{GUID}` had separately failed as non-admin (only Administrators may specify names).

## Windows OS semantics versus G3 acceptance

Microsoft documents that window stations contain clipboards and desktops, and each Windows client session is associated with its **own** interactive station named `WinSta0`. Accordingly, the owner `alexa` Session 2 `WinSta0` and guest Session 3 `WinSta0` have the same string name but are different session-scoped objects. This is a useful **OS architectural boundary**, consistent with SID1009 Session 3 named-mutex PASS and headless Edge/CDP startup PASS. It does **not alone** prove all real owner screen/clipboard access is denied, that previously inherited handles are absent, or that named pipes/network/owner services cannot expose owner data.

Sources (Microsoft):
- [Window Stations](https://learn.microsoft.com/en-us/windows/win32/winstation/window-stations)
- [Remote Desktop Sessions](https://learn.microsoft.com/en-us/windows/win32/termserv/terminal-services-sessions)
- [Window Station and Desktop Creation](https://learn.microsoft.com/en-us/windows/win32/winstation/window-station-and-desktop-creation)
- [CreateWindowStationW](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-createwindowstationw)

## Архитектурный вывод и следующий шаг

Имена/metadata собственных станций проверены. Повторять эту inspection для получения того же результата не нужно.
Новая private station не создана; её создание не является обязательной целью session-based Candidate.
Текущий выбор описан в [session decision](G3_SESSION_BOUNDARY_OUTCOME_DECISION_2026-10-15.md).

Дальше — свои guest GUI/clipboard positive, owner negative и конечная chain по подпунктам 2/3/6/8
[актуального плана](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md). Ручной guest login принят; old unattended requirement не применяется.
Прежние варианты/рекомендации сохранены [в архиве](G2_G3_SUPERSEDED_GUIDANCE_2026-10-15.md#station_guidance).
Фактический JSON и documented OS semantics выше не изменены.
