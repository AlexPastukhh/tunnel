# Observatory → Tab Notifier: синхронизация начала и завершения работы

**Status: SOURCE-ONLY / owner deployment не проверен (2026-10-18).** Изменения подготовлены в Fortis Repo; текущая установленная версия Observatory и Tampermonkey не проверялись. Пользователь может уже иметь первые два патча — не применять их повторно вслепую.

## Требуемое поведение

ChatGPT —(started/progress/checkpoint/completed)—> Repo inbox —> Observatory (Markdown)
—(read-only статус)—> Tab Notifier в том же Chat ID: 🔵 работа / 🔷 готово / 🔹 просмотрено.
В режиме только DOM используются штатные ⏳ / ● / ✓ без внешнего источника.

Если DOM ChatGPT тормозит, новое принятое started/progress/checkpoint может включить синее 🔵 (работа из Observatory), а completed переключает **индикатор** вкладки в завершённое синее 🔷/🔹. Другие события не принимаются за успешное завершение. Это сообщение чата, а не гарантия сохранённого результата. Внешний completed **не запускает очередные сообщения и автоотправку**, то есть не вызывает onFinished с его побочными действиями. При новой ручной отправке старое completed не применяется.

Если Edge полностью заморозил JS вкладки, Tab Notifier не сможет запросить Observatory до пробуждения: это ограничение браузера.

## Связь и безопасность

- GET /api/observer-pair?session=... — только с owner-токеном Observatory. Создаёт отдельный read-only ключ для конкретной ручной сессии.
- GET /api/observer-status?session=... — только с X-Fortis-Observer-Key, выдаёт conversation_id, reporting_session_id, event, sequence, accepted_unix, source. Не раскрывает summary, файлы или owner-токен.
- Ключ привязки копировать только в меню Tab Notifier в **соответствующем чате**, а не в сообщение ChatGPT или Repo/G2.
- Непривязанные чаты не опрашивают Observatory. При смене URL проверяется Chat ID. Одно и то же Chat ID в двух вкладках использует общую привязку GM storage, что соответствует привязке беседы, а не отдельной вкладки.

## Подготовленные файлы в Fortis Repo

- ../store.py, ../server.py, ../client.js, ../index.html — новый status API, обновлённый промпт, кнопка «Код для Tab Notifier».
- notifier-observatory-v1.patch — применимый патч к upstream Tab Notifier v5.6.1. Не коммитить и не пушить без отдельного разрешения.
- observatory-completion.js — новый JS-модуль, добавляемый патчем в src/observatory-completion.js.
- updated-local-loader.user.js — шаблон изменённого Tampermonkey-загрузчика с нужными grants.
- test_bridge.js — синтетические тесты fallback и привязки.

Патч SHA-256: f8ff932bd40a8f25fc77d290151d541555d2f458f35c5364a1d3e8e35c2a0ca3. Проверено применение к GitHub upstream main, синтаксис изменённых файлов и отсутствие вызова очереди/автоотправки во внешнем finish.

## Порядок owner-обновления (НЕ выполнен)

1. Основной Windows-пользователь проверяет исходники V1, ACL и стабильность owner-private установленного каталога. Проверенные pins ниже; старый OWNER_INSTALL.md всё ещё закрепляет прежнюю версию и не подходит для бездумного повторного запуска. Не выполнять Python из доступного Repo RW.
2. После отдельного согласования остановки только Observatory V1 (Ctrl+C в его собственной owner-консоли), owner копирует проверенные файлы в protected AppData и перезапускает этот же сервер. Не останавливать другие службы, не менять ACL/mount.
3. В основном Windows-пользователе проверить локальный checkout Tab Notifier. Если есть свои незакоммиченные правки, их сохраняют до следующего шага. Применение патча в локальном checkout (НЕ Git commit/push):

~~~powershell
Set-Location C:\Users\alexa\tabnotifier-fileautosend-autochat
$patch = 'C:\Users\alexa\Repos\tunnel\observatory\v1\notifier-adapter\notifier-observatory-v1.patch'
git apply --check $patch
# Если проверка успешна и рабочие изменения сохранены:
git apply $patch
# Второй патч добавляет синие отличительные индикаторы Observatory:
$colorPatch = 'C:\Users\alexa\Repos\tunnel\observatory\v1\notifier-adapter\notifier-observatory-color-v1.patch'
git apply --check $colorPatch
git apply $colorPatch
npm run build
npm run test
npm run build:check
~~~

4. В Tampermonkey у существующего local-loader дописать grants GM_getValue, GM_setValue, GM_deleteValue, GM_xmlhttpRequest и connect 127.0.0.1. Полный образец — updated-local-loader.user.js; путь @require на локальный построенный chatgpt-tab-notifier.user.js оставить. При необходимости обновить/переустановить userscript, если Tampermonkey закешировал старый @require.
5. В разблокированной owner-панели Observatory для нужной сессии нажать «Код для Tab Notifier»; скопированный JSON вставить через меню Tab Notifier «Fortis: привязать текущий чат». Ключ не передавать в переписку.
6. Сквозной тест: новая работа → Notifier working → новое принятое completed → Notifier fresh/viewed даже при запаздывании DOM. Проверить старый completed, чужой Chat ID, отключение и отсутствие запуска очереди. Не использовать приватную переписку для тестовых данных.

SHA-256 после изменения:

~~~text
server.py    198ad7c6ee5fe8192fba6e3556bb270bb7a3767f393db16728f486084c1c849f
store.py     8fa0078610f0a8b9e348cd252cfa0250ec099e88551737efadc7843be51ca5c3
emit.py      26d8a393a79984d23ae8b3444bf21753a6f90162b88a50c446d8514aa03cded3
index.html   accb4cda7e68e3676362148b0be473464b85994ae0d5ab606ab205c6b1551d60
client.js    6dc3a7e5b17e9d7ad592735c45df24c02fe9ba4925bec8b74bdef95061d14d0d
style.css    a681d2992a28e1f4878a553f3cc431aeb72a57398d052cd816aba97263af33e0
~~~

Эти SHA относятся к текущему source snapshot; повторно проверять перед owner копированием. Контент приложения в Windows до owner pin/update **не изменился**.

## Verification / open gates

На source-only этапе пройдены Python HTTP tests 21/21, Node bridge test, 47 смежных Observatory tests, независимое применение патча к upstream и проверки JS-синтаксиса. Сохранение пошаговых событий и новый текст промпта проверены отдельными регрессионными тестами. Вспомогательный мониторный тест подтвердил, что завершение извне не запускает queued auto-send.

Не проверено и не заявляется: реальный Edge, обновление Tampermonkey, native owner API после upgrade, Windows reparse/ACL после upgrade, реальное получение индикатором completion в работающей вкладке.


## Различимые цвета: собственный Tab Notifier vs Observatory

Дополнительный патч notifier-observatory-color-v1.patch (SHA-256:
f6fc3db67eed6545d5ceb57f0814414aebf4817f1785e03945e7b883c089511d)
применяется ПОСЛЕ базового notifier-observatory-v1.patch.

- Обычный Tab Notifier без изменений: ⏳ — working, ● + красный favicon — непрочитанный ответ, ✓ + серый favicon — просмотренный.
- Observatory после нового принятого completed: 🔷 + синий favicon — ответ завершён по событию чата, вкладка в фоне; 🔹 + тёмно-синий favicon — вкладка просмотрена.
- Системное уведомление при внешнем завершении подписывается «Fortis Observatory — завершено по событию чата», а не обычным «ChatGPT — ответ готов».
- Новая отправка сообщения снова переключает вкладку в ⏳. Просмотр не стирает указание источника. Прежний механизм очереди/автоотправки не вызывается от внешнего completed.
- Значок/подпись и источник служат лишь **визуальным различением заявленного события**: никакого доказательства сохранения полного ответа.

Если базовый patch ранее уже применён в локальном checkout Tab Notifier, НЕ применяй его снова. В основном Windows PowerShell, только после проверки своей рабочей копии:

~~~powershell
Set-Location C:\Users\alexa\tabnotifier-fileautosend-autochat
$colorPatch = 'C:\Users\alexa\Repos\tunnel\observatory\v1\notifier-adapter\notifier-observatory-color-v1.patch'
git status --short
git apply --check $colorPatch
# Только если git apply --check успешен и нет конфликтов с сохранёнными своими правками:
git apply $colorPatch
npm run build
npm run test
npm run build:check
~~~

**Менять метаданные Tampermonkey loader ещё раз не нужно:** достаточно уже добавленных
GM_getValue, GM_setValue, GM_deleteValue, GM_xmlhttpRequest и @connect 127.0.0.1.
Но может потребоваться обновить локальный @require в Tampermonkey, если файл закеширован.

Новый регрессионный тест: в Fortis Repo выполнить
node observatory/v1/notifier-adapter/test_color.js <checkout-after-both-patches>.
В проверенном временном каталоге: COLOR_AND_SOURCE_REGRESSION_TEST PASS.
Тест проверяет синие favicon/текст вкладки, сохранение цвета после просмотра,
обычные уведомления, метку источника и отсутствие действий очереди.
Нативную проверку действующего Edge пользователь выполняет отдельно.


## Тестовые переключатели начала И завершения — третий патч

После базового патча notifier-observatory-v1.patch и цветового
notifier-observatory-color-v1.patch применяется **третий** патч:
notifier-observatory-toggle-v1.patch. SHA-256:
72ca3a953791b1b6e75f2a0585df40deb40deae4f7b5692d9debdd6477ba9ca6

Новые пункты меню Tampermonkey в Tab Notifier:

- «Fortis: переключить DOM (начало и конец)» — включает/выключает штатные сигналы начала и завершения ответа.
- «Fortis: переключить Observatory (начало и конец)» — включает/выключает старт по started/progress/checkpoint и завершение по completed.
- «Fortis: показать источники состояния» — показывает оба текущих переключателя.

После нажатия каждого переключателя появляется окно с состоянием обоих
источников. По умолчанию оба включены. Четыре комбинации:
оба включены, только DOM, только Observatory, оба выключены.
Режим хранится в sessionStorage по Chat ID в **текущей вкладке Edge**,
переживает её перезагрузку, но не влияет на другие вкладки.
Новый Chat ID по умолчанию использует оба способа.

Переключатели определяют источник как НАЧАЛА, так и КОНЦА работы
для индикатора вкладки, а НЕ включение всей программы или автоотправки.
В режиме «только Observatory» клик Send и DOM вообще не включают working:
лишь свежее принятое started/progress/checkpoint из Observatory показывает
синюю метку начала 🔵, а completed завершает 🔷/🔹.
В режиме «только DOM» начало и конец определяются браузерным детектором.
В режиме «оба выключены» ни один из двух источников не меняет
индикатор начала/окончания. Очередь/загрузка и другие функции остаются.
Старые события из архива не должны повторно включать работающую вкладку:
проверяются последовательность, время приёма и текущий Chat ID.

Внешнее завершение не запускает onFinished очереди сообщений.
При отключённом Observatory новые HTTP-запросы не выполняются;
поздние ответы игнорируются. Ключ привязки при выключении сохраняется.

В owner PowerShell только после установки первых ДВУХ патчей, сверки
рабочей копии и сохранения своих незакоммиченных изменений:

~~~powershell
Set-Location C:\Users\alexa\tabnotifier-fileautosend-autochat
$togglePatch = 'C:\Users\alexa\Repos\tunnel\observatory\v1\notifier-adapter\notifier-observatory-toggle-v1.patch'
git status --short
git apply --check $togglePatch
# Если проверка успешна, и нет конфликтов с пользовательскими изменениями:
git apply $togglePatch
npm run build
npm run test
npm run build:check
~~~

Tampermonkey Local Loader с уже добавленными GM_grants менять заново
не нужно. Сохранённый @require остаётся тем же. После сборки обновить
локальный userscript и вкладку ChatGPT. Для чистого сравнения переключи
режим **перед началом новой генерации**.

Регрессионный тест test_toggle.js проверяет четыре комбинации,
сохранение режима, изоляцию Chat ID, отсутствие опроса Observatory при
выключении, блокировку позднего HTTP-ответа, штатное и внешнее начало/завершение.
Этот ФАЙЛ ПАТЧА ОБНОВЛЁН на месте: не устанавливай его старую копию.
Если третий патч ранее не ставился, применяй его один раз ПОСЛЕ первых двух.

Ограничение текущего V1: read-only API возвращает только ПОСЛЕДНЕЕ
принятое событие. Если started и completed оба попали между двумя
запросами Tab Notifier, он может пропустить переход начала и поэтому
не завершить этот цикл в режиме «только Observatory». Для коротких
работ это остаётся отдельным будущим улучшением: возвращать несколько
последних коротких event-маркеров без summary. Сквозной live-тест в Edge
для этой редакции пока не проводился.


## Миграция установленного старого переключателя

Если в локальной рабочей копии Tab Notifier видны isDomFinishEnabled и
«Fortis: переключить завершение DOM», значит старый третий патч уже
применён. НЕ применяй новый notifier-observatory-toggle-v1.patch сверху.

Вместо этого используй миграционный патч:
notifier-observatory-upgrade-old-toggle.patch
SHA-256: fac7e625d25bc20db9ee3dbc977387085d0521a122535fce146f09a0dfd998e9

В PowerShell основного Windows-пользователя:

~~~powershell
Set-Location C:\Users\alexa\tabnotifier-fileautosend-autochat
$migrate = 'C:\Users\alexa\Repos\tunnel\observatory\v1\notifier-adapter\notifier-observatory-upgrade-old-toggle.patch'
git status --short
git apply --check $migrate
if ($LASTEXITCODE -ne 0) { throw 'Патч не подходит. Не применять.' }
git apply $migrate
if ($LASTEXITCODE -ne 0) { throw 'Применение не завершено.' }
npm run build
npm run test
npm run build:check
~~~

Первые два патча повторно не применять. Не использовать git reset,
checkout, clean или принудительное git apply. Все существующие
незакоммиченные пользовательские правки сохраняются как есть.
Пересборка нужна только после успешного применения миграции.

В синтетическом checkout, восстановленном из GitHub upstream и
первых двух патчей плюс прежний переключатель, миграция успешно
применяется и на LF, и на CRLF; результат совпадает с новой версией
третьего патча. Регрессионные тесты двух источников, четырёх режимов,
цветов и мостика прошли. На реальной Windows/Edge установке пока
не проверялось. Уже дополненный GM-разрешениями Tampermonkey Local
Loader менять снова не нужно; обновить userscript/@require после сборки.


## Совместимая миграция после git apply --check: src/response-monitor.js hunk failure

Для Windows-копий с уже установленным старым переключателем
isDomFinishEnabled, когда строгая миграция
notifier-observatory-upgrade-old-toggle.patch (SHA fac7e625...)
не проходит на одном хунке src/response-monitor.js около
console.debug/finishAnswer, используйте ВМЕСТО НЕЁ новый
notifier-observatory-upgrade-compat.patch.

SHA-256: ed6251918174e0932a2db2458cc8f6e7118c54cdb6378c02125f6666a059dce0

Патч использует узкий контекст, не меняет текст/локализацию лога
и не требует чистого Git checkout. Сохраняет исходный контракт
armAnswer() без обязательного boolean true при разрешённом DOM.
Режимы DOM/Observatory, смена цвета, работа с наблюдением и тесты
совпадают с новой версией переключателя.

Проверен git apply --check и git apply с синтетическими вариантами:
обычный старый переключатель, без пустой строки возле finishAnswer,
с изменённой строкой лога, обе правки вместе, Windows CRLF.
После применения каждый вариант прошёл тесты двух источников, четырёх
режимов, цветов; базовый тест Observatory bridge также прошёл.

В PowerShell основного Windows-пользователя (предыдущий строгий патч
не применять), после отдельной проверки пользовательских изменений:

~~~powershell
Set-Location C:\Users\alexa\tabnotifier-fileautosend-autochat
$p = 'C:\Users\alexa\Repos\tunnel\observatory\v1\notifier-adapter\notifier-observatory-upgrade-compat.patch'
(Get-FileHash $p -Algorithm SHA256).Hash
git apply --check $p
if ($LASTEXITCODE -ne 0) { throw 'Проверка совместимого патча не прошла, остановиться.' }
git apply $p
if ($LASTEXITCODE -ne 0) { throw 'Ошибка применения, остановиться.' }
npm run build
if ($LASTEXITCODE -ne 0) { throw 'Сборка не прошла.' }
npm run test
if ($LASTEXITCODE -ne 0) { throw 'Тесты не прошли.' }
npm run build:check
if ($LASTEXITCODE -ne 0) { throw 'Сверка сборки не прошла.' }
~~~

Если совместимая проверка тоже не проходит, не включать -3/--reject/--force
и не применять патч по частям. Нужны только нужные локальные фрагменты
src/response-monitor.js для подготовки точного исправления.


## Финальная миграция под присланный реальный response-monitor.js

У пользователя Windows код отличается от реконструированного старого
переключателя: комментарий перед armTimer уже есть и комментарий
«DOM still detects the start...» уже находится перед
isDomFinishEnabled(). Поэтому обе миграции
notifier-observatory-upgrade-old-toggle.patch и
notifier-observatory-upgrade-compat.patch на его рабочей копии НЕ прошли.
Они не применялись, потому что использовался git apply --check.

ИСПОЛЬЗУЙ ТОЛЬКО notifier-observatory-upgrade-exact-v1.patch, в котором
ожидаются оба этих комментария на существующих местах.

SHA-256: 00391ad29b4ea901b1cf8ed9c7535ec2eac380be466e10b05999d9825d6f29e3

Проверено применение к синтетическому checkout, восстановленному из
upstream v5.6.1 + базовый/цветовой/старый toggle с комментариями,
совпадающими с присланным пользователем response-monitor.js.
Отдельно проверено применение с CRLF в трех изменённых файлах,
JS-синтаксис, test_toggle.js, test_color.js, test_bridge.js.

PowerShell (проверка останавливает дальнейший код только ВНУТРИ
условия; запускать единым блоком, чтобы сообщение об успехе
не выполнялось после ошибки):

~~~powershell
Set-Location C:\Users\alexa\tabnotifier-fileautosend-autochat
$patch = 'C:\Users\alexa\Repos\tunnel\observatory\v1\notifier-adapter\notifier-observatory-upgrade-exact-v1.patch'
$expected = '00391AD29B4EA901B1CF8ED9C7535EC2EAC380BE466E10B05999D9825D6F29E3'
if ((Get-FileHash -LiteralPath $patch -Algorithm SHA256).Hash -ne $expected) { throw 'Неверный SHA-256' }
git apply --check $patch
if ($LASTEXITCODE -ne 0) { throw 'Проверка git apply не пройдена — не применять.' }
git apply $patch
if ($LASTEXITCODE -ne 0) { throw 'Ошибка применения патча.' }
npm run build
if ($LASTEXITCODE -ne 0) { throw 'Ошибка сборки.' }
npm run test
if ($LASTEXITCODE -ne 0) { throw 'Тесты не пройдены.' }
npm run build:check
if ($LASTEXITCODE -ne 0) { throw 'Проверка build:check не пройдена.' }
Write-Host 'Патч применён; сборка и проверки прошли.'
~~~

Примечание: исходные версии файлов в Linux Repo и установленный
Windows runtime Tab Notifier — разные копии. Реальное применение
Windows owner ещё не подтверждено.
