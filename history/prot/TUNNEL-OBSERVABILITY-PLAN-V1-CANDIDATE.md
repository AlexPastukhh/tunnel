# Tunnel Observability Plan — V1 Candidate Revision

Status: CANDIDATE REVISION — NOT COMMITTED
Date: 2026-10-08
Source committed baseline: `TUNNEL-OBSERVABILITY-PLAN.md` (V0 working baseline)
Related GUI baseline: `TUNNEL-OBSERVABILITY-GUI-PROTOTYPES.md`

## 1. Target / version resolution

- Target plan: overall Tunnel + chat/run observability composition in `TUNNEL-OBSERVABILITY-PLAN.md`.
- Source version: V0 — current accepted working plan before this review iteration.
- V0 remains unchanged and is the committed baseline for this transaction.
- No later candidate/committed version was found in the project root.
- This file is V1-candidate. It must not be treated as committed until explicit user commit.
- If committed, the corresponding Prototype 5 section in the GUI plan must be revised consistently.

## 2. Review provenance

### R-LIVE-ETA-1
- Target: V0, specifically chat/run liveness, heartbeat contract, session-state logic and future Prototype 5.
- Date/order: 2026-10-08, before this candidate revision.
- Scope: step events, ETA baseline, heartbeat/tool activity, liveness inference, data-boundary and GUI warning semantics.
- Limitation: no separate UI-observer transport or run/step protocol was implemented end-to-end in the review.

### Post-review user clarifications
- UC-1: ChatGPT UI activity must be usable as an additional evidence source, including when Tunnel/MCP delivery fails.
- UC-2: chat should not be burdened with remembering periodic heartbeats; infer activity from real Tunnel/tool requests plus explicit step announcements.
- UC-3: explicit `step_finish` is not needed for MVP; the next `step_start`, `waiting_user` or `run_finish` can close the prior step.

## 3. User Needs

- N-1: Quickly see whether the Tunnel, control plane and MCP target are healthy.
- N-2: Understand whether a specific long-running chat/run is still progressing or has become suspiciously stale.
- N-3: Distinguish chat/run staleness from MCP/session/Tunnel/local-process failure.
- N-4: See the current work step, elapsed time and why the system considers it normal, late or suspicious.
- N-5: Preserve useful incident/history evidence without turning observability into a privileged control plane.
- N-6: Keep production work reliable; observability experiments must not silently break or replace the current working path.

## 4. Fundamental Requirements

- FR-1: Monitoring surfaces stay localhost-only and do not become externally exposed control APIs.
- FR-2: P1/P2 remain out-of-band; production MCP path is unchanged until a separate canary stage.
- FR-3: Do not persist runtime keys, raw tool payloads, full stdout/stderr, prompts/transcripts or file contents by default.
- FR-4: Evidence and hypotheses must be displayed separately; lack of one signal is not automatically proof of chat death.
- FR-5: Tunnel health, MCP/session health, active request/process state and chat/run state remain distinct layers.
- FR-6: Real Tunnel/tool/process activity counts as liveness evidence automatically.
- FR-7: A step ETA is a contextual lateness baseline, not a completion-time promise.
- FR-8: Periodic chat heartbeat is not an MVP obligation.
- FR-9: ChatGPT UI activity/step visibility is a valid independent evidence source when available.
- FR-10: Step transitions should require minimal chat bookkeeping; `step_finish` is not mandatory in MVP.

## 5. Existing committed decisions / proposal identity

The original plan had no stable Proposal IDs. V1-candidate bootstraps IDs without changing the historical meaning of V0.

- P-1@V0 — read-only localhost dashboard over existing health/metrics. Status: committed / implemented.
- P-2@V0 — persistent history + incident capture/export. Status: committed / implemented in current P1/P2.
- P-3@V0 — transparent MCP observability proxy, developed offline then on canary. Status: committed direction / pending.
- P-4@V0 — session heartbeat canary with `monitor_register`, `monitor_heartbeat`, `monitor_finish`. Status: committed direction / pending.
- P-5@V0 — process/AV correlation. Status: committed direction / pending.
- P-6@V0 — controlled production rollout after canary evidence. Status: committed direction / pending.

## 6. Confirmed review findings

- F-1 / confirmed problem: step lateness and run liveness are different signals.
- F-2 / confirmed problem: heartbeat through the same MCP/session path is not independent evidence when that path fails.
- F-3 / confirmed problem: strict wall-clock heartbeat cadence cannot be assumed for every model/tool phase.
- F-4 / confirmed problem: step granularity must be constrained or elapsed/ETA comparisons become unstable.
- F-5 / confirmed problem: arbitrary free-text step/status payloads can violate the observability data boundary.
- F-6 / confirmed problem: ETA revisions must not erase the original timing evidence.
- F-7 / uncertainty: model ETA calibration quality is unknown before real samples exist.
- F-8 / uncertainty: exact run/session correlation is not yet guaranteed by the Tunnel.
- F-9 / process improvement from UC-1: use ChatGPT UI activity as another evidence channel rather than adding heartbeat burden immediately.

No review finding changes N-1..N-6. UC-1..UC-3 add/clarify FR-8..FR-10 rather than silently redefining the original needs.

## 7. Proposal changes

### P-7@V1-candidate — Explicit Run/Step Marker Contract
DERIVED_FROM: P-4@V0
Addresses: F-1, F-3, F-4, F-5, UC-2, UC-3
Traceability: N-2, N-4, N-5; FR-3, FR-4, FR-7, FR-8, FR-10

Candidate content:
- A run may expose `run_start`, `step_start`, optional `step_update`, `waiting_user`, and `run_finish`.
- `step_finish` is not required: next `step_start`, `waiting_user`, or `run_finish` closes the active step.
- Each step has a broad `step_kind`, short sanitized label, initial ETA range/upper bound, and confidence.
- One meaningful active phase at a time; long tool/process waits use explicit waiting/external-wait semantics.
- The initial ETA and later revisions are both retained.
- Ordinary human-visible milestone text may carry the step marker; no periodic heartbeat spam is required.

Status: preferred candidate.

### P-8@V1-candidate — Passive ChatGPT UI Activity Observer
DERIVED_FROM: UC-1
Addresses: F-2, F-9
Traceability: N-2, N-3, N-4; FR-4, FR-9

Candidate content:
- Observe assistant UI activity passively: visible step marker changes, assistant text/streaming activity, and response completion state.
- Prefer metadata-only telemetry: timestamp, local run correlation token if available, visible step number/kind, streaming true/false.
- Do not require screenshots, cursor/focus control, or storing the full assistant text.
- UI silence is weak evidence; UI activity is strong positive evidence that the run continued at that moment.

Status: preferred candidate.

### P-9@V1-candidate — Run Activity Fusion / Evidence Model
DERIVED_FROM: P-1@V0, P-3@V0, P-7@V1-candidate, P-8@V1-candidate
Addresses: F-1, F-2, F-8, UC-1, UC-2
Traceability: N-2, N-3, N-4; FR-4, FR-5, FR-6, FR-9

Candidate content:
- Fuse three evidence families without collapsing them into one opaque score:
  1. Chat UI telemetry;
  2. explicit run/step markers;
  3. Tunnel/MCP/tool/process telemetry.
- Show at least two primary dimensions:
  - Step timing: ON TIME / LATE / VERY LATE;
  - Liveness evidence: ACTIVE / QUIET / NO RECENT SIGNAL / WAITING TOOL / WAITING USER / PATH DEGRADED / UNKNOWN.
- Overall warning may be derived, but the evidence that caused it stays visible.
- If UI remains active while MCP/session telemetry degrades, prefer “RUN ACTIVE / PATH DEGRADED”.
- If UI and run signals are quiet but a correlated tool/process remains active, prefer “WAITING TOOL / ACTIVE PROCESS”.
- If all run signals are quiet, no tool/process is active, Tunnel is healthy, and ETA is materially exceeded, use “STALE CANDIDATE”, not “DEAD”.

Status: preferred candidate.

### P-10@V1-candidate — ETA / Lateness Model
DERIVED_FROM: F-1, F-4, F-6, F-7
Traceability: N-2, N-4; FR-4, FR-7

Candidate content:
- Minimum fields: `duration_class`, `expected_max_seconds`, `confidence`; optional `expected_min_seconds` for display.
- Preserve `step_started_at`, initial estimate, and every ETA revision.
- ETA revisions may reduce/increase confidence but never reset elapsed time.
- Initial heuristic bands are candidate-only, not calibrated truth:
  - <= expected max: normal timing;
  - > expected max: late;
  - substantially beyond expected max: very late / increased suspicion.
- Exact thresholds should remain configurable until real data is collected.

Status: preferred candidate.

### P-11@V1-candidate — Optional Heartbeat Experiment
REVISED_FROM: P-4@V0
ALTERNATIVE_TO: mandatory heartbeat contract
Traceability: N-2, N-3; FR-4, FR-8

Candidate content:
- Remove periodic heartbeat from the required chat contract.
- Keep heartbeat only as a later canary experiment if UI + step + tool/process activity leaves material blind spots.
- A missed in-band heartbeat never means DEAD.

Status: deferred alternative; excluded from MVP candidate composition.

### P-4@V0 disposition in V1-candidate
The old mandatory heartbeat canary is REMOVED FROM CANDIDATE and proposed to be SUPERSEDED by P-7 + P-8 + P-9 + P-10. It remains in history and is not erased.

## 8. Proposal Groups / relations

### PG-LIVE-1 — Run Activity & Step Liveness bundle
Members: P-7, P-8, P-9, P-10
Purpose: answer N-2/N-3/N-4 without mandatory periodic heartbeat.

Relations:
- P-7 RECOMMENDED_WITH P-8.
- P-9 REQUIRES P-7 and P-8 for the preferred candidate behavior.
- P-9 RECOMMENDED_WITH P-3 for exact per-run request correlation.
- P-10 REQUIRES P-7 because ETA belongs to the step contract.
- P-11 ALTERNATIVE_TO the mandatory-heartbeat portion of P-4 and is not selected for MVP.
- P-7 + P-8 + P-9 + P-10 proposed SUPERSEDES P-4 for Prototype 5 semantics.
- P-5 remains RECOMMENDED_WITH P-3 and P-9 for process/AV evidence.
- P-6 still REQUIRES successful canary acceptance for any production-path changes.

Relation-graph check:
- No hard dependency cycle found.
- No selected proposals conflict with FR-1..FR-10.
- Exact per-run Tunnel attribution remains weaker without P-3; this is tracked as QRP-C-R-2 rather than hidden.

## 9. Proposal-level QRP

### QRP-P-1 — target P-7 — Problem
Source: R-LIVE-ETA-1 / F-4
Issue: unconstrained step granularity makes ETA comparison unstable.
Status history: introduced on V0 review; mitigated in V1-candidate by one-active-phase semantics and explicit waiting states; requires canary validation before resolved.

### QRP-P-2 — target P-7/P-8 — Problem
Source: R-LIVE-ETA-1 / F-5
Issue: free-text monitoring labels can store unnecessary user content.
Status history: introduced on V0 review; mitigated in V1-candidate by categorical fields + short sanitized labels; persistence/export redaction must be tested.

### QRP-P-3 — target P-10 — Problem
Source: R-LIVE-ETA-1 / F-6
Issue: ETA revisions can indefinitely move the threshold.
Status history: introduced on V0 review; mitigated in V1-candidate by immutable step start, original ETA, and revision history.

### QRP-R-1 — target P-8 — Risk
Source: UC-1 + architectural review
Condition: ChatGPT DOM/UI structure changes or observer loses access.
Consequence: UI activity evidence can disappear even though the run continues.
Mitigation: treat UI silence as weak evidence, version the observer, and retain Tunnel/tool evidence independently.
Status: open, non-blocking for fixture design.

### QRP-Q-1 — target P-8 — Question
Source: UC-1
Question: which implementation should carry passive UI telemetry: userscript, browser extension, or another local integration?
Why important: affects reliability, maintenance and permissions.
Status: open; non-blocking for data-model/UI fixture work, blocking before real UI-observer implementation.

### QRP-Q-2 — target P-9 — Question
Source: R-LIVE-ETA-1 / F-8
Question: how is a visible ChatGPT run reliably correlated with Tunnel requests?
Status: open; non-blocking for coarse prototype, blocking for exact per-run attribution.

## 10. Proposal Group QRP

### QRP-PG-R-1 — target PG-LIVE-1 — Risk
Source: R-LIVE-ETA-1 / F-1,F-2,F-3
Condition: evidence channels disagree or one becomes silent.
Consequence: a single scalar “risk” can hide whether the problem is lateness, path degradation or lack of evidence.
Mitigation in candidate: show step timing and liveness evidence separately; overall warning is secondary.
Status: mitigated in V1-candidate, requires UI validation.

### QRP-PG-R-2 — target PG-LIVE-1 — Risk
Source: UC-2
Condition: chat emits too many micro-steps or too few giant steps.
Consequence: poor usability and weak ETA meaning.
Mitigation: broad step-kind contract, one active meaningful phase, next step auto-closes previous step.
Status: open for canary calibration.

## 11. Composition-level QRP

### QRP-C-Q-1 — Composition question
Source: R-LIVE-ETA-1 + UC-1
Question: does the product require an absolute guarantee of chat liveness when both UI and normal MCP activity are silent?
Current candidate answer: no such absolute guarantee is claimed. UI activity is selected as the secondary evidence channel; silence remains UNKNOWN/STALE CANDIDATE, not DEAD.
Status history: open after review; narrowed by UC-1/UC-2 in V1-candidate; non-blocking for MVP.

### QRP-C-R-2 — Composition risk
Source: current V0 telemetry limits
Condition: current P1/P2 has global Tunnel metrics but no proven per-run request correlation.
Consequence: “this request belongs to this visible chat step” may be inferred incorrectly when several chats are active.
Mitigation: coarse correlation only before P-3; exact attribution waits for canary proxy/session correlation.
Status: open; non-blocking for UI/step fixtures, blocking for exact per-run claims.

### QRP-C-P-1 — Composition problem
Source: R-LIVE-ETA-1 + UC-2
Issue: V0 Prototype 5 makes periodic heartbeat a primary contract, creating unnecessary chat bookkeeping and ambiguous failure-domain evidence.
Violated intent: N-2/N-3 plus FR-4/FR-8 in the revised semantic foundation.
Status history: confirmed against V0; proposed resolved by PG-LIVE-1 in V1-candidate; remains open until candidate commit/implementation validation.

## 12. User Assistance

No user action is required for the next fixture/state-machine/GUI work.

Later user decision only if QRP-C-Q-1 changes to a requirement for stronger-than-UI evidence when the normal MCP path is broken. That would reopen a separate monitoring-channel proposal and materially expand scope.

## 13. Candidate Revised Composition

### Retained unchanged
- P-1 read-only localhost health/metrics dashboard.
- P-2 persistent history + incident capture/export.
- P-3 proxy developed offline and then canary-only before any production change.
- P-5 process/AV correlation.
- P-6 controlled production rollout.

### Revised / new selected bundle
- P-7 explicit run/step marker contract.
- P-8 passive ChatGPT UI activity observer.
- P-9 evidence fusion / liveness-state model.
- P-10 ETA/lateness model.

### Removed from MVP candidate but retained in history
- P-4 mandatory periodic heartbeat canary.
- P-11 optional heartbeat experiment remains deferred, not selected.

### Preferred Prototype 5 name
`Run Activity & Step Liveness canary` instead of `heartbeat canary`.

## 14. Candidate Prototype 5 user scenario

### P5-S1 — Is the current chat/run still progressing?

**Задача пользователя:** понять, жив ли длинный run и на каком шаге он находится, не заставляя чат слать периодические heartbeat-сообщения.

**Мотивация:** долгий шаг может быть нормальным, зависшим или продолжать работу в ChatGPT UI при сломанном MCP/Tunnel path.

**Действие пользователя:** открыть Run Activity view для нужного run/chat.

**Реакция программы:**
- показать текущий явный step marker и его начальный/актуальный ETA;
- показать elapsed и Step timing отдельно от Liveness evidence;
- учитывать последние Tunnel/tool/process requests автоматически;
- учитывать ChatGPT UI activity/streaming/visible step changes, если observer доступен;
- показывать причину вывода, например “VERY LATE but active process” или “UI active / MCP path degraded”;
- не объявлять run dead только по тишине.

**Результат:** пользователь отличает медленный активный шаг, ожидание tool/process, деградацию MCP path и действительно подозрительно тихий run.

**Критерий успеха:** в тестовых сценариях одинаково долгий step классифицируется по-разному в зависимости от evidence: LATE/ACTIVE при живой активности и STALE CANDIDATE только при существенном ETA overrun + отсутствии UI/tool/process evidence.

### P5-S2 — Tunnel path сломался, но ChatGPT UI продолжает работу

**Задача пользователя:** понять, что проблема относится к MCP/session/Tunnel path, а не к полной остановке run.

**Мотивация:** реальная наблюдаемая проблема может затрагивать один chat/session при живом локальном Tunnel.

**Действие пользователя:** открыть проблемный run после timeout/init error.

**Реакция программы:** если UI observer видит новые assistant output/step markers, а correlated MCP activity остановилась или показывает lifecycle error, вывести “RUN ACTIVE / PATH DEGRADED” и показать оба источника evidence отдельно.

**Результат:** пользователь не перезапускает глобальный Tunnel только потому, что один chat path перестал выполнять tools.

**Критерий успеха:** synthetic/canary test с UI activity + отсутствием MCP events не классифицируется как dead/stale run.

## 15. Alternative compositions

### AC-1 — Separate monitoring connector/channel
Content: explicit step telemetry goes through a second monitoring-only connector independent of production MCP.
Pros: stronger structured independence from the production path.
Cons: extra connector, lifecycle, permissions and operational complexity; still needs correlation with visible chat.
Relation: ALTERNATIVE_TO P-8 as the secondary evidence channel; may be RECOMMENDED_WITH P-8 only if future evidence justifies the extra complexity.
Status: viable but not selected; reopen only if UI observer proves insufficient or QRP-C-Q-1 becomes a stronger guarantee.

### Excluded alternative — mandatory periodic in-band heartbeat
Reason excluded: conflicts with UC-2/FR-8 and does not independently diagnose failure of its own path. Historical P-4 remains recorded.

## 16. Need / FR coverage re-check

- N-1: covered by P-1/P-2/P-3.
- N-2: covered by PG-LIVE-1; exact certainty is intentionally limited when all evidence is silent.
- N-3: covered by P-8/P-9 plus P-3 for exact request attribution.
- N-4: covered by P-7/P-9/P-10.
- N-5: covered by FR-1/FR-3 and sanitized observer/step payload rules.
- N-6: covered by FR-2, canary sequencing and P-6.

FR-1..FR-10 are covered by the selected candidate composition. No selected proposal requires a production-path change before canary.

## 17. Composition Delta vs V0

- UNCHANGED: P-1 read-only dashboard.
- UNCHANGED: P-2 history/incidents.
- UNCHANGED: P-3 transparent proxy as offline/canary work before production.
- UNCHANGED: P-5 process/AV correlation.
- UNCHANGED: P-6 controlled rollout.
- REMOVED FROM CANDIDATE: P-4 mandatory periodic heartbeat contract.
- ADDED: P-7 explicit run/step marker contract. Source: R-LIVE-ETA-1 F-3/F-4 + UC-2/UC-3.
- ADDED: P-8 passive ChatGPT UI activity observer. Source: UC-1 + R-LIVE-ETA-1 F-2.
- ADDED: P-9 multi-source evidence fusion with separate lateness/liveness states. Source: F-1/F-2/F-8.
- ADDED: P-10 ETA/lateness model preserving original estimates and revisions. Source: F-1/F-6/F-7.
- ADDED as DEFERRED ALTERNATIVE: P-11 optional heartbeat experiment. Source: lineage from P-4 after UC-2.
- REVISED GROUP: Prototype 5 changes from “heartbeat canary” to “Run Activity & Step Liveness canary”.
- REVISED RELATION: exact per-run Tunnel attribution is explicitly dependent on P-3/correlation rather than assumed from global P1 metrics.

## 18. QRP history / status summary

- QRP-P-1: open after R-LIVE-ETA-1 -> mitigated in V1-candidate, pending validation.
- QRP-P-2: open after R-LIVE-ETA-1 -> mitigated in V1-candidate, pending redaction test.
- QRP-P-3: open after R-LIVE-ETA-1 -> mitigated in V1-candidate by immutable timing history.
- QRP-R-1: introduced in V1-candidate, open.
- QRP-Q-1: introduced in V1-candidate, open; implementation-choice question.
- QRP-Q-2: still applicable from V0 correlation uncertainty; blocking only for exact per-run claims.
- QRP-PG-R-1: mitigated by separate timing/liveness indicators; pending UI validation.
- QRP-PG-R-2: open until step granularity is tested on canary data.
- QRP-C-Q-1: narrowed by UC-1/UC-2; MVP does not claim absolute liveness when all channels are silent.
- QRP-C-R-2: still applicable until P-3 correlation exists.
- QRP-C-P-1: confirmed against V0; candidate remediation is PG-LIVE-1, not yet committed.

No finding was invalidated in this iteration. The mandatory-heartbeat direction is not deleted from history; it is excluded from the candidate composition because later user clarification changed the preferred solution.

## 19. Unresolved decisions

- QD-1: implementation vehicle for P-8 UI observer: userscript vs extension vs another local browser integration. Category: желательно согласование before implementation; non-blocking for fixtures/schema.
- QD-2: exact server-issued run/session correlation handshake for P-9/P-3. Category: high suitability for autonomous design in canary; non-blocking now, blocking before exact attribution claims.
- QD-3: calibrated ETA warning thresholds. Category: high suitability for autonomous provisional defaults; final calibration deferred until real samples exist.

## 20. Candidate Version / Transaction Status

Candidate label: V1-candidate
Source: V0 + R-LIVE-ETA-1 + UC-1 + UC-2 + UC-3
Transaction status: CANDIDATE ONLY — NOT COMMITTED

Commit pre-check status:
- Need coverage: PASS for candidate scope.
- FR coverage: PASS for candidate scope.
- Relation graph: no hard cycle/conflict found.
- Unsatisfied dependency: P-3 remains required before exact per-run Tunnel attribution; this does not block fixture/UI work.
- Blocking QRP for current next step: none.
- Blocking QRP before production-grade per-run liveness claims: QRP-Q-2 / QRP-C-R-2.

On explicit commit, V1-candidate should become V1 and the committed `TUNNEL-OBSERVABILITY-PLAN.md` plus Prototype 5 section of `TUNNEL-OBSERVABILITY-GUI-PROTOTYPES.md` should be updated from this composition while preserving V0 history.
