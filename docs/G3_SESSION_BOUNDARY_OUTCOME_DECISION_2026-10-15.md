# G3 — решение об отдельной guest Windows-сессии, 2026-10-15

**Отдельная non-admin guest Windows-сессия — предпочтительный Candidate. G3 BLOCKED; конечная native конфигурация не принята.**

[Актуальный план](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md) владеет условиями, разрешениями, критериями и очередью проверок.
Эта страница объясняет выбор реализации; она не вводит вторую матрицу обязательных требований.

## Основание решения

В предыдущем owner-session варианте SID1009 не мог создавать нужные named objects; Edge завершался на ProcessSingleton.
В собственной guest Session3 пользователь подтвердил SID1009/non-admin, Local mutex,
Edge headless startup с собственным temporary profile, CDP port-file и cleanup.
Names-only inspection показал собственную guest WinSta0; это разные session-scoped объекты с owner WinSta0.

Это аргумент в пользу простой session-based схемы. Он не доказывает owner GUI/clipboard DENY,
полный native MCP в этой session, отсутствие owner capabilities через handles или защиту loopback API.
Доказательства и их ограничения: план E05/E07/E10–E13.

## Текущие принятые условия и границы

Пользователь разрешил ежедневный guest login/start/switch-back и работу с собственными guest GUI/clipboard.
Основная защищаемая GUI/clipboard область — сессия alexa, включая обычные окна без elevation.
Формальная таблица разрешений и все уточнения поддерживаются [в одном месте](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md#целевая-политика-что-разрешено-и-что-защищаем).

- Unattended cold boot и запуск до guest login не являются обязательным UX gate.
- Private station, headless, Job/supervisor/IPC broker — варианты реализации, а не цели сами по себе.
- Нужны guest positive и owner negative evidence в выбранной конфигурации; владельческий clipboard/экран в тестах не читаются.
- Owner API оценивается по опасным действиям и чувствительным данным; безопасная диагностика допустима при доказанной семантике/версии.
- OS-изоляция G2 и whole-chat route isolation принимаются раздельно.
- Новый standalone private-station путь рассматривается только при выявленном недостатке session-based решения.

## Следующая проверка

Следовать подпунктам 2/3/6/8 [плана](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md) и его условиям controlled test launch.
Старый owner-session `Start-G2PrivateWindow.ps1 -Mode Launch` не является принятым Session3 launcher.
Owner WinSta0/Default ACL, службы/задачи, privileged broker и существующие туннели этим решением не меняются.

## Предыдущая редакция

[Предыдущий текст решения](G2_G3_SUPERSEDED_GUIDANCE_2026-10-15.md#session_decision) сохранён целиком.
В нём встречаются отменённый HARD PRODUCT GATE без ежедневного входа и обязательный supervisor:
это исторические варианты, не текущие условия. Raw evidence остаётся в исходных датированных файлах.
