# Review Log — Chat liveness / step ETA

Date: 2026-10-08

## Object / scope
Review of the proposed run/step monitoring design: step events, duration estimates, activity signals, and GUI warning states. Current P1/P2 was checked only to confirm that this run/step layer is not implemented yet.

## Result
The core idea is useful: a per-step expected duration is a better baseline than one global inactivity timer. Several design corrections are required before implementation.

## Confirmed problems
P-1 — Step lateness and liveness are different signals. If a step exceeds its estimate while a tool or local process is still active, or fresh activity signals continue, the correct state is LATE / ACTIVE, not stale. Keep two dimensions: lateness and liveness evidence.

P-2 — A heartbeat sent through the same monitored path is not independent evidence. If that path has a session or transport failure, both normal work and heartbeat can disappear together. A missed in-band heartbeat therefore means UNKNOWN. A separate monitoring path is needed only if the product must distinguish chat activity from failure of the normal tool path.
