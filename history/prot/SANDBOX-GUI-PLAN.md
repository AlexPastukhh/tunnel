# План отдельного GUI для ChatGPT

Статус: проектирование
Дата: 2026-10-07

## Цель

ChatGPT должен иметь отдельную GUI-среду на том же физическом ПК, где можно автономно:
- открывать приложения и браузер;
- делать screenshots;
- использовать мышь и клавиатуру;
- тестировать UI;
- не забирать focus/cursor у основного desktop пользователя.

## Основная идея

Обычная Windows interactive session не является надёжной boundary для независимого GUI.
Virtual Desktops и второй монитор не дают отдельный input/focus session.

Первый кандидат для прототипа:
- Windows Sandbox;
- управление Sandbox с HOST через отдельный restricted broker;
- Microsoft winapp CLI как возможный механизм автоматизации Sandbox.

Перед реализацией точный текущий синтаксис и ограничения winapp нужно заново проверить по официальной документации, потому что инструмент preview/развивается.
## Целевая архитектура

```text
ChatGPT
  -> отдельный Sandbox Control plugin / broker
  -> существующий Secure MCP Tunnel на HOST
  -> restricted host-side controller
  -> winapp CLI --on sandbox
  -> Windows Sandbox
```

Ключевая идея: OpenAI runtime key, Desktop Commander и unrestricted host shell не нужно помещать внутрь Sandbox.

Sandbox plugin должен предоставлять только Sandbox-targeted операции и не давать произвольный HOST shell.

Пример capability surface:
- sandbox.start / stop;
- sandbox.run;
- sandbox.list_windows / inspect;
- sandbox.invoke / set_value;
- sandbox.send_keys / click;
- sandbox.screenshot / record;
- контролируемый folder share только после локального разрешения.

## HOST boundary

Наличие Sandbox не должно означать автоматический доступ к основному desktop.
HOST остаётся filesystem/CLI/process/log/config/API средой.
GUI на основном HOST:
- не делать screenshots самостоятельно;
- не двигать мышь;
- не кликать;
- не отправлять keyboard/hotkeys;
- не использовать clipboard injection;
- не активировать окна для взаимодействия.

После завершения Sandbox-capable части:
1. остановиться;
2. объяснить, зачем нужен HOST;
3. запросить отдельное разрешение;
4. только после разрешения использовать HOST.

HOST GUI требует ещё одного, отдельного разрешения поверх обычного HOST CLI/filesystem доступа.

## Ограничения Windows Sandbox

- disposable: состояние исчезает после закрытия;
- одна Sandbox instance одновременно;
- writable mapped folders являются реальным доступом к host-файлам;
- cold connect/reconnect может кратковременно повлиять на focus;
- real input/recording требуют активного, не заблокированного host session.

Если нужны persistence, несколько сред, checkpoints или долгоживущая dev-машина — использовать Hyper-V VM.

## Прототип

1. Проверить Windows Sandbox feature.
2. Проверить актуальную официальную winapp документацию.
3. Установить winapp на HOST из официального источника.
4. Запустить Sandbox без sensitive mappings.
5. Проверить screenshot, Notepad, UIA, typing/click внутри Sandbox.
6. Проверить реальное отсутствие вмешательства в основной desktop.
7. После этого проектировать restricted Sandbox Control MCP.
