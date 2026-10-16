# G2-G — остановка теста и проверка rollback, 2026-10-13

**Статус:** PASS в описанном scope. Тестовый G2 остановлен; регистрация, отдельный credential и рабочие исходники сохранены. Полная изоляция сессии остаётся OPEN по G2-F; production security acceptance отсутствует.

## Проверка восстановления обёртки

Проверка выполнена через restricted G2 MCP под SID 1009 на отдельном уникальном файле RW.
Backup: `C:\Users\Public\Documents\FortisHostG1Probe\RW\g2-stdio-gate.before-headless-20261013.py.bak`.
SHA-256 backup и восстановленной временной копии: `001D2BEF2A515AE48D01A0E4421598FB4F87C0D5E8EEAAA399A0118593A93F61`.
Self-test backup: `PASS: secret-related names absent from Node environment`.
Рабочая headless-обёртка не менялась: SHA-256 `146E60B028276F871353A113571306002942461F0446E519A63B28DCC068418D`.
Временная копия `probe-g2g-1791872009403-f3h8ry-rollback.py` удалена; отсутствие подтверждено после остановки.
Это восстановление backup на временной копии, а не отмена UI-настройки или проверка всех Windows ACL/profile/credential rollback сценариев.

Первый MCP вызов вернул timeout. Перед повтором проверены absence временного файла и сохранность live headless setting; затем повторный запуск получил явный PASS. Timeout не выдаётся за неисполнение.

## Проверенная остановка G2

До остановки подтверждены SID, executable name, parent relation, CreationDate и открытые process handles:
- Tunnel PID 27324, profile fortis-host-g2-test, Created 2026-10-13T05:25:18.9614770Z.
- Wrapper Python PID 16160, parent 27324, Created 2026-10-13T05:25:20.4680250Z.
- Desktop Commander Node PID 14112, parent 16160, Created 2026-10-13T05:25:20.6725930Z.
Все три принадлежат SID `S-1-5-21-303538662-3368424508-2654684973-1009`.

Остановка запрошена из ограниченного G2: после identity guards завершён test Node; проверенные wrapper/tunnel handles ожидались с bounded wait и fallback termination. Ответ MCP потерян при закрытии stdio (transport_closed/eof); результат установлен независимой проверкой, без повторной остановки.
После: все исходные три процесса отсутствуют, test profile process отсутствует, loopback 60267 не слушает.

## Рабочие маршруты после остановки

| Маршрут | PID / CreationDate | healthz / readyz |
|---|---|---|
| HOST desktop-commander | 5580 / 2026-10-13T02:59:43.4833490Z, без изменения | 200 / 200 |
| Repo repo-mode | 23904 / 2026-10-13T03:00:34.2137140Z, без изменения | 200 / 200 |

Owner runtime keys, profiles, ACL, Docker mounts, plugin audience/permissions и регистрации не менялись. Отзыв test credential не выполнялся: он нужен для дальнейших испытаний.
Удалены только свои временные rollback/probe объекты; reusable wrappers, backup и marker fixtures сохранены.

## Продолжение

Новый запуск G2 требует локального ввода отдельного runtime-ключа в PowerShell пользователя FortisHostG1; значение не извлекать из owner key или памяти процесса. При запуске применяется сохранённая headless wrapper.
Далее G3 — адресные проверки альтернативных путей под restricted token. Отдельно остаётся фактическая route isolation: старый HOST и native Repo доступны этому чату, выбор @G2 не является обязательной границей.
Связанные доказательства: [G2-E/F](G2_E_F_EVIDENCE_2026-10-13.md), [UI/runtime](../runtime/host-g2/README.md).
