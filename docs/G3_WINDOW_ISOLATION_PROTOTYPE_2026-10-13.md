# G3 — отдельная оконная станция: прототип, 2026-10-13

**SYNTHETIC PASS / LIVE NOT APPLIED. G3 OPEN, G4 не принят.**
[JSON evidence](G3_WINDOW_ISOLATION_PROTOTYPE_2026-10-13.json) · [исходник и локальный Preview](../runtime/host-g2/window-isolation/README.md).

## Что доказано
Actual SID 1009, non-admin, создал отдельную unnamed noninteractive station с явным private DACL.
Fresh PowerShell child запускался с lpDesktop=private-station\default, без наследования handles, внутри kill-on-close Job.
Node и его обычный PowerShell descendant остались на этой станции; Visible=false.
Workspace RW, runtime read и mutation DENY, отсутствие secret-related env names PASS.
Installed Edge headless с новым temporary profile, своим loopback HTTP и CDP прошёл synthetic localStorage/DOM проверку; default browser sandbox сохранён.
Edge exit 0; собственные scratch/profile удалены. Nine fresh station/desktop opens после synthetic deny получили Win32 5; original DACL restored через retained controller handles, private objects closed.
Повторное create-only создание той же private station подтвердило отсутствие прежних объектов; final helper compile/synthetic cleanup PASS.
Actual G2 AccessCheck prospective owner WinSta0/default DACL: 4 station и 5 desktop rights DENY. Owner WRITE_DAC before/after ALLOW. Это прогноз в памяти, не live deny.
Actual G2 DUP_HANDLE к owner HOST/Repo DENY 5, к старой собственной G2 консоли ALLOW 0. Поэтому её retained handles нельзя оставлять при переходе.
Clipboard/screen content не читались; никакой автоматизации основного Windows GUI.

## Что НЕ принято
Действующий G2 всё ещё на WinSta0. Его текущие clipboard/screen/WRITE_DAC rights не закрыты.
Private station сама по себе не запрещает открыть owner WinSta0 заново, а изменение DACL не отзывает старые handles.
Прототип controller под SID 1009 сохранял старые handles для synthetic rollback; он не является production launcher.
Credentialed new-runtime launch, owner-controlled supervisor, live original-DACL backup/CAS rollback и реальный переход ещё не реализованы/не проверены.
При пересоздании owner logon session нужны новая приёмка ACL и обязательный защищённый entry path; старый interactive G2 launcher не годится как итоговый путь.
Owner local APIs, широкие chat tool routes, service/SMB остаток остаются отдельными G3 gates.

## Подготовленный локальный шаг
Preview-G2WindowBoundary.ps1 поддерживает только Preview. Скрипт и два компонента pinned SHA256; компилируются именно проверенные bytes.
Preview читает security metadata WinSta0/default, строит target SID 1009 deny в памяти и проверяет сохранение owner WRITE_DAC.
Процессный inventory WTS + fallback TOKEN_USER: non-elevated HOST определяет пять живых G2 PID, но пять других process owners UNKNOWN / Win32 5. Их безопасность не предполагается.
Local elevated owner Preview временно включает SeDebugPrivilege только у своего процесса для metadata и затем отключает его. ACL writes=0, ProcessesStopped=0, SecretsPrompted=false.
Запустить Preview в свежей elevated PowerShell пользователя alexa; вернуть JSON. Для Preview ничего не закрывать, ключ/пароль не вводить.
Preview SHA256: 2465814CA6E07F2DA03D182E1B372D516933137F2DA046007AAEC0F45C74FA07.
После complete privileged inventory подготовить owner-only запуск, backup/rollback; затем закрыть только все старые G2 account процессы и выполнить точечный переход с actual-token/Edge/MCP приёмкой.

## Observer и источники
На 2026-10-13T14:13:56.4685864Z (21:13 Asia/Bangkok) HOST 5580, Repo 23904, G2 28148 сохранили прежние CreationDate, health/ready 200/200.
Original owner station/default SDDL совпадают с срезом до тестов; main ACL unchanged. Не менялись owner launchers/keys/private folders, Docker/services/tasks/shares/Sites; commit/push не выполнялся.
[Windows stations](https://learn.microsoft.com/en-us/windows/win32/winstation/window-stations) · [Process binding/handles](https://learn.microsoft.com/en-us/windows/win32/winstation/process-connection-to-a-window-station) · [Object rights](https://learn.microsoft.com/en-us/windows/win32/winstation/window-station-security-and-access-rights) · [Jobs](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects) · [WTS inventory permissions](https://learn.microsoft.com/en-us/windows/win32/api/wtsapi32/nf-wtsapi32-wtsenumerateprocessesw).
