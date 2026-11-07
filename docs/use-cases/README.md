# Tunnel — локальные Use Cases

Только Tunnel-specific operations. Общие правила GitHub/CI/Windows и авторизации
из [главного реестра Fortis](https://github.com/AlexPastukhh/fortis-container/blob/main/docs/use-cases/README.md)
(UC-CONT-002/003 обязательны), предметные технические контракты — в
[документации Tunnel](../README.md). Не читать весь реестр Fortis.

| ID | Ситуация | Результат | Owner |
| --- | --- | --- | --- |
| UC-TUN-001 | Нужно проверить/применить Windows Repo Guards | Точный guarded identity и ограниченная owner verification | [Guards](guards.md#uc-tun-001) |
| UC-TUN-002 | Требуется безопасный reconnect Tunnel/Windows worker | Проверенный reconnect или STOP без подмены профиля | [Reconnect](reconnect.md#uc-tun-002) |
