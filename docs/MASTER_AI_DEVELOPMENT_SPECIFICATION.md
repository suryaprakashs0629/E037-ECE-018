# Campus Walkie-Talkie Channel and Time-Slot Allocation Engine
## Master AI Development Specification — Team E037

**Team members:** Surya Prakash.S; Sudarshan V.
**Version:** 2.0 | **Target:** Windows localhost | **Stack:** Python 3.10–3.12, Flask, Jinja2, HTML/CSS/JS, SQLAlchemy, MySQL

---
## 0. Instructions to the AI developer

Build a complete, functioning application—not a static UI prototype. Read this specification and the actual official Team E037 sample ZIP before implementing the evaluator.

- Treat the official Team E037 sample-pack README and exact file formats as authoritative for command-file processing and evaluation.
- Do not hardcode sample request IDs, group IDs, dates, channel assignments or expected results.
- Keep the allocation engine independent of Flask routes and templates. Website and command-file paths must reuse the same domain services wherever semantics overlap.
- Preserve official command syntax, processing order, inclusive slot convention, reason codes, output filenames, column order and sorting.
- Do not invent missing CSV rows or commands. The actual channels.csv, groups.csv and commands.txt must be loaded from the team's ZIP during implementation.
- Deliver migrations, tests, seed scripts, setup instructions, documentation and a working Windows localhost launch process.
- Do not leave placeholder buttons, fake metrics or nonfunctional exports.

Source precedence: (1) official Team E037 README and evaluation contract; (2) original ECE-018 brief and college clarifications; (3) this document for website architecture and UX; (4) developer choices only where they do not alter the above.

Source limitation: the official README was inspected. The actual CSV and command-file rows must be loaded from the ZIP. The README states that expected output files are not included.

## 1. Project identity and purpose

Official project name: Campus Walkie-Talkie Channel and Time-Slot Allocation Engine. Team ID: E037. Team members: Surya Prakash.S and Sudarshan V.

The application manages campus walkie-talkie channel requests, validates them, allocates channels across half-hour slots, enforces priority and interference constraints, records outcomes, and generates official CSV outputs. It is a software simulation only: it does not transmit RF signals, control radios or measure signal strength.

- Manage channel and group master data.
- Accept requests from authorised website users and official command files.
- Validate, merge and schedule requests deterministically.
- Enforce channel availability, adjacency, continuity, priority and late-arrival pre-emption.
- Generate the exact official evaluation CSV files.
- Provide a local admin/group-user website with schedules, conflicts, reports and audit history.

Version 1 non-goals: physical radio integration, cloud hosting, native mobile app, public self-registration, external identity provider, and any exception that allocates channel 16.

## 2. Official radio and time configuration

| Item | Official requirement |
| --- | --- |
| Total channels | 16 |
| Allocatable channels | 1–15 |
| Reserved channel | 16; never allocated, including emergency requests |
| Starting frequency | 446.00625 MHz |
| Spacing | 12.5 kHz = 0.0125 MHz |
| Frequency formula | 446.00625 + (channel_no - 1) × 0.0125 MHz |
| Slots per day | 48 |
| Slot duration | 30 minutes |
| Slot numbering | 1–48; slot 1 = 00:00–00:30; slot 48 = 23:30–24:00 |
| Daily capacity | 15 × 48 = 720 allocatable channel-slots |

MANDATORY inclusive slot convention: duration = end_slot - start_slot + 1. Slots 18–25 are 8 slots and pass the duration check. Slots 18–26 are 9 slots and must be rejected with DURATION_LIMIT. Do not implement end-exclusive slots in the official evaluator. Website time inputs must convert to official slot numbers explicitly and consistently.

| Request | Duration | Expected validation |
| --- | --- | --- |
| 18–25 | 8 | Pass duration validation |
| 18–26 | 9 | DURATION_LIMIT |
| 1–1 | 1 | One slot |
| 47–48 | 2 | Two slots |

## 3. Official input file schemas

### channels.csv

| Column | Type / format | Rule |
| --- | --- | --- |
| channel_no | Integer | Primary key, 1–16 |
| frequency_mhz | Decimal, 5 dp | Formula in Section 2 |
| spacing_khz | Decimal | 12.5 |
| is_emergency | Boolean | True only for channel 16 |

### groups.csv

| Column | Type / format | Rule |
| --- | --- | --- |
| group_id | GRP-nn string | Primary key; do not hardcode IDs |
| group_name | String | Display name |
| category | Enum | SECURITY, MEDICAL, EVENTS, MAINTENANCE |
| priority_rank | Integer | 1 highest through 4 |
| contact_name | String | Informational only |
| contact_mobile | 10 digits | Starts 6–9; informational only |

| Category | Priority rank | Order |
| --- | --- | --- |
| SECURITY | 1 | Highest |
| MEDICAL | 2 | Second |
| EVENTS | 3 | Third |
| MAINTENANCE | 4 | Lowest |

The official pack contains 15 groups across four categories. Load the actual group records from groups.csv; never assume group IDs or names.

## 4. Official commands.txt contract

One command per physical line: COMMAND_NAME|arg1|arg2|... Process top-to-bottom. Ignore blank lines and lines beginning with #. Preserve physical line numbers for diagnostics.

| Command | Arguments | Meaning |
| --- | --- | --- |
| LOAD_CHANNELS | file | Load channels.csv |
| LOAD_GROUPS | file | Load groups.csv |
| REQUEST | request_id/group_id/date/start_slot/end_slot/channels_needed/fixed_channels | Submit request |
| ALLOCATE | YYYY-MM-DD | Validate, merge and allocate requests submitted so far for that date |
| PRINT_TABLE | YYYY-MM-DD | Output daily allocation table |
| PRINT_UTILISATION | YYYY-MM-DD | Output daily utilisation |
| PRINT_CONFLICTS | ALL | Output conflict log for all days |

fixed_channels = ANY means automatic selection. A semicolon-separated channel list means those exact channels in every slot; it is not a soft preference. If the list contains 16, reject RESERVED_CHANNEL. Validate duplicates, range and count consistency.

- Parse and validate command field counts and types.
- Trim surrounding whitespace but preserve meaningful identifiers.
- Validate dates as YYYY-MM-DD and slots as integers 1–48.
- Retain command order and monotonically increasing submission sequence.
- Malformed input must produce a line-numbered diagnostic and must not corrupt previously committed state.
- Never execute shell commands, Python or arbitrary code from uploaded text.

## 5. Exact official output contract

### allocation_table.csv

One row per allocated channel per slot. Sort by date, then slot, then channel_no. Exact header order:

```text
date,slot,slot_start,channel_no,frequency_mhz,group_id,request_id
```

### utilisation.csv

One row per day. channel_slots_available is 720. utilisation_pct = channel_slots_used / 720 × 100, rounded to 2 decimal places. Exact header order:

```text
date,channel_slots_used,channel_slots_available,utilisation_pct
```

### conflict_log.csv

One row per rejected, merged or pre-empted request, in processing order. Exact header order:

```text
date,request_id,group_id,reason,detail
```

| Reason | Meaning | detail |
| --- | --- | --- |
| UNKNOWN_GROUP | Group absent from master | NONE |
| DURATION_LIMIT | More than 8 inclusive slots | NONE |
| TOO_MANY_CHANNELS | More than 3 channels needed | NONE |
| RESERVED_CHANNEL | Fixed list contains 16 | NONE |
| MERGED | Merged into earlier same-group request | Earlier request ID |
| NO_CHANNEL | No valid complete allocation | First slot number that could not be served |
| PREEMPTED | Whole lower-priority allocation removed by late request | Pre-empting request ID |

Do not rename files, change headers, add output columns, alter reason codes, change details or reorder rows. Output must be deterministic for identical input.

## 6. Allocation engine — mandatory rules

### 6.1 Validation

1. Unknown group → UNKNOWN_GROUP.
2. Duration greater than 8 inclusive slots → DURATION_LIMIT.
3. channels_needed greater than 3 → TOO_MANY_CHANNELS.
4. Explicit fixed channel 16 → RESERVED_CHANNEL.
5. Also validate date, slot bounds 1–48, positive channel count, fixed-list syntax, duplicates, valid range and fixed-list count. For malformed values, return a parser/validation diagnostic without inventing an official conflict reason.

### 6.2 Same-group overlapping requests

Before allocation for a date, merge overlapping requests from the same group. The merged request covers the union of occupied slots, uses the larger channels_needed value (not the sum), and keeps the earlier request ID. Log the later request as MERGED; detail is the earlier request ID.

| Request | Group | Slots | Demand |
| --- | --- | --- | --- |
| REQ-A | GRP-06 | 35–38 | 1 |
| REQ-B | GRP-06 | 37–40 | 2 |
| Merged result | GRP-06 | 35–40 | 2; earlier ID retained |

### 6.3 Initial allocation order

1. Consider requests submitted before that date's ALLOCATE command.
2. Validate requests.
3. Merge same-group overlapping requests.
4. Sort SECURITY → MEDICAL → EVENTS → MAINTENANCE.
5. Within a category preserve submission order (FIFO).
6. Allocate in that order.

## 7. Channel rules, continuity and atomicity

- A channel cannot be assigned to two different groups in the same slot.
- Different groups cannot use adjacent channel numbers in the same slot.
- Same-group adjacent channels are allowed.
- Channel 16 is never allocated.
- ANY: choose the lowest valid channels, subject to continuity.
- Fixed list: use exactly those channels in every slot; never substitute another set.
- A request must receive its full channel demand in every covered slot.

Adjacency conflict exists when date and slot match, groups differ, and channel numbers are equal or differ by exactly one. Same-group adjacent channels are allowed.

Continuity: in the next slot first retain channels used by the same request in the previous slot if still valid; then add the lowest valid channels until demand is met. If a clash forces a move to another channel, keep that changed channel in later slots where valid; do not jump back merely because the original channel becomes free. Fixed channels remain exact in every slot.

All-or-nothing: if any required slot fails, discard every tentative allocation row for that request and log NO_CHANNEL with the first unserved slot. Do not retain partial allocations. Previously committed unrelated requests remain intact.

## 8. Late arrivals and pre-emption — official rule

A REQUEST command after that date's ALLOCATE command is a late arrival. Only a late request may trigger pre-emption. First try ordinary complete allocation. If it cannot fit, identify lower-priority allocations overlapping its slots.

1. Victim selection: lowest category priority first (MAINTENANCE before EVENTS before MEDICAL before SECURITY); among the same category choose the latest submitted.
2. Tentatively remove one victim's entire allocation.
3. If this makes the late request fit completely, commit both the removal and late request.
4. Log the victim as PREEMPTED; detail is the pre-empting request ID.
5. The pre-empted request is not retried.
6. Do not remove a victim if that removal does not make the late request fit.
7. If no eligible single victim resolves it, log late request as NO_CHANNEL with first unserved slot.
8. Initial pre-ALLOCATE requests cannot pre-empt one another.

This exact late-arrival behaviour overrides the earlier generic pre-emption proposal. Do not implement broader pre-emption.

## 9. Official processing diagrams

### 9.1 Shared architecture

```text
              TEAM E037 — CAMPUS WALKIE-TALKIE ENGINE
                              |
          +-------------------+-------------------+
          |                                       |
     WEB APPLICATION                         COMMAND RUNNER
     Flask + Jinja                           commands.txt
          |                                       |
    Login / RBAC                            Parser + CSV loaders
          |                                       |
    Admin / Group UI                         REQUEST / ALLOCATE
          |                                       |
          +-------------------+-------------------+
                              |
                    SHARED DOMAIN SERVICES
                              |
        Validator → Merger → Priority/FIFO scheduler
                              |
        Channel allocator + adjacency + continuity
                              |
              Late-arrival pre-emption manager
                              |
                  Transaction coordinator
                              |
                         MySQL ORM
                              |
          Allocations | Conflict logs | Audit history
                              |
      allocation_table.csv / utilisation.csv / conflict_log.csv
```

### 9.2 Official command processing

```text
START → Read commands.txt top-to-bottom
  → Ignore blank/comment lines
  → LOAD_CHANNELS / LOAD_GROUPS → validate master data
  → REQUEST → record request and submission sequence
       → before ALLOCATE: queue by date
       → after ALLOCATE: late-arrival path; allocate now;
                          if needed try eligible pre-emption
  → ALLOCATE(date)
       → validate → merge same-group overlaps
       → priority + FIFO → allocate atomically
  → PRINT_TABLE / PRINT_UTILISATION / PRINT_CONFLICTS
  → Write exact three CSV outputs → END
```

### 9.3 Per-request allocation

```text
Receive → Parse and validate → Determine ANY or fixed channels
  → For each covered slot in ascending order:
       retain previous request channels if valid
       add lowest valid channels to meet demand
       check same-channel and cross-group adjacency
  → All slots satisfied?
       YES: commit every row atomically
       NO: discard all tentative rows; log NO_CHANNEL
            with first failed slot
```

### 9.4 Late pre-emption

```text
Late request → Validate → Try normal complete allocation
  → Success: commit
  → Failure: find lower-priority overlapping victims
       sort lowest category first, latest submission first
       tentatively remove one whole victim
       does request now fit completely?
           YES: commit victim removal + late request; log PREEMPTED
           NO: restore tentative state; try next eligible victim
  → no victim resolves: log late request NO_CHANNEL
```

### 9.5 Website workflow

```text
Open localhost → Login → Role check
  ├─ ADMIN → Admin dashboard → manage masters/review requests
  └─ GROUP_USER → Own-group dashboard → submit request
                    → server validation → pending request
Admin review → Approve or reject
  → approved → shared allocation service
  → result → timetable + logs + reports + notifications
```

## 10. Roles and permissions

Use exactly two access roles: ADMIN and GROUP_USER. SECURITY, MEDICAL, EVENTS and MAINTENANCE are operational group categories, not login roles.

| Capability | ADMIN | GROUP_USER |
| --- | --- | --- |
| System-wide dashboard | Yes | No |
| Manage users/groups/channels | Yes | No |
| Submit request | Optional/admin enabled | Own group |
| View all requests | Yes | No |
| View own-group requests | Yes | Yes |
| Edit pending request | Yes, audited | Own group |
| Approve/reject | Yes | No |
| Run allocation | Yes | No |
| View all schedules/reports/conflicts | Yes | No |
| View own allocations | Yes | Yes |
| Change allocation constraints | No | No |

Emergency website extension: only users explicitly enabled by an admin may submit emergency requests; justification required; priority equivalent to SECURITY but original category retained for reporting. Channel 16 remains unavailable. The official REQUEST command schema has no emergency fields, so do not modify that syntax; treat emergency metadata as website-only unless the college issues an updated contract.

## 11. Website pages and interactions

Design: dark charcoal/navy sidebar, light content, blue accents; desktop-first and responsive; collapsible sidebar; breadcrumb; notifications; profile/logout; search/filter/pagination; loading, empty and error states; confirmation dialogs. Use text labels as well as status colours. All metrics must be database-backed, never fabricated.

| Page | Required behaviour |
| --- | --- |
| Login | Username/password, generic failure, secure session, role redirect, logout |
| Admin dashboard | Real counts, pending requests, allocations, utilisation, conflicts, category charts, recent events |
| Group dashboard | Own-group requests, upcoming allocations, notifications, submit shortcut |
| Group management | Create/edit/deactivate groups; category, code, name, status |
| User management | Create/edit/deactivate users, assign role/group, reset password, emergency permission |
| Channel masters | Show channels 1–16 and frequency; mark channel 16 reserved |
| Request management | Filter, inspect, approve/reject with comment, view validation |
| Submit request | Date, start/end slot, demand, ANY/fixed channels, purpose; server validation |
| Allocation runs | Select date, confirm, execute, show allocated/failed/pre-empted totals |
| Schedule | Day/channel/slot timetable with filters |
| Conflict logs | Official reason, request, group, date, detail, processing order |
| Reports | Allocation, utilisation, group/category/request status |
| Command import | Upload, parse, preview, line diagnostics, confirm |
| Command export | Exact official CSV output downloads |
| Audit logs | Actor, action, entity and timestamp |
| Backup/settings | Admin-only database backup/restore with confirmation |

### Button contracts

| Action | Required result |
| --- | --- |
| Submit request | Validate, save PENDING_REVIEW, create event, notify admin |
| Edit pending | Revalidate, save revision, retain prior event |
| Approve | Verify state, record actor/time, call shared allocator according to workflow |
| Reject | Store reason/comment, update status, notify group |
| Run allocation | Acquire schedule lock, create run, execute deterministic algorithm, commit and show summary |
| Import | Safely parse, preview and validate; never execute arbitrary code |
| Export | Generate exact official CSV schema and ordering |
| Deactivate | Block future access/requests but preserve history |
| Restore backup | Confirm, validate, log and restore safely |

## 12. Request lifecycle and database model

| Status | Meaning |
| --- | --- |
| PENDING_REVIEW | Submitted; waiting for admin |
| REJECTED | Admin rejected |
| APPROVED | Approved and ready for allocation |
| ALLOCATED | Fully allocated |
| ALLOCATION_FAILED | Could not be allocated completely |
| PREEMPTED | Whole allocation removed by late higher-priority request |
| CANCELLED | Authorised cancellation |

Keep website statuses separate from official conflict reason codes. Every state transition creates a request event and, where relevant, audit, notification and allocation-history records.

| Table | Purpose / key fields |
| --- | --- |
| roles | id, name |
| users | id, full_name, username, password_hash, role_id, group_id, is_active, can_submit_emergency |
| groups | id, group_code, group_name, category, priority_rank, contact fields, is_active |
| channels | channel_no, frequency_mhz, spacing_khz, is_emergency |
| requests | id, request_code, group_id, date, start_slot, end_slot, channel_count, fixed_channels, purpose, status, submission sequence |
| request_events | request_id, actor, event_type, old/new state, comment, timestamp |
| allocation_runs | id, date, run_type, started/finished, status, actor |
| allocations | run_id, request_id, date, slot, channel_no, group_id |
| allocation_history | assignment identity, event, old/new values, timestamp |
| conflict_logs | date, request_id, group_id, reason, detail, sequence, run_id |
| notifications | user_id, title, body, read state, timestamp |
| audit_logs | actor, action, entity, entity_id, timestamp, safe metadata |
| import_batches / import_rows | file hash, uploader, status, physical line, raw text, parse status, message |
| system_settings | key, value, updated_by |

```text
roles 1 ─── * users
groups 1 ── * users
groups 1 ── * requests
requests 1 ─ * request_events
requests 1 ─ * allocations
allocation_runs 1 ─ * allocations
allocation_runs 1 ─ * conflict_logs
channels 1 ─ * allocations
users 1 ─ * notifications
users 1 ─ * audit_logs
import_batches 1 ─ * import_rows
```

Integrity: unique username and group code; channel number 1–16 in master but allocation only 1–15; foreign keys; indexes on request date/status/group and allocation date/slot/channel. Lock the affected schedule/date during allocation to avoid concurrent race conditions. Preserve history; do not hard-delete historical records.

Site extension conflict: earlier website planning included two independent campus sites, but the official README and command schema inspected here do not contain a site field. First implement the exact single-schedule evaluation adapter. If the two-site website extension remains required, isolate it as optional website-only functionality and do not change official CSV output.

## 13. Backend architecture and project structure

Use a modular Flask app. Routes handle HTTP and authorization; services contain business rules; models represent persistence; command runner calls the same domain services.

```text
campus_walkie_talkie_engine/
├── run.py
├── config.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── app/
│   ├── __init__.py
│   ├── extensions.py
│   ├── models/
│   ├── auth/
│   ├── admin/
│   ├── group_user/
│   ├── requests/
│   ├── schedule/
│   ├── reports/
│   ├── imports/
│   ├── services/
│   │   ├── command_parser.py
│   │   ├── master_data_loader.py
│   │   ├── request_validator.py
│   │   ├── request_merger.py
│   │   ├── priority_scheduler.py
│   │   ├── channel_allocator.py
│   │   ├── adjacency_checker.py
│   │   ├── continuity_manager.py
│   │   ├── preemption_manager.py
│   │   ├── allocation_transaction.py
│   │   ├── output_writer.py
│   │   └── report_service.py
│   ├── templates/
│   └── static/
├── migrations/
├── tests/unit/
├── tests/integration/
├── tests/acceptance/
├── official_sample_data/
├── exports/
├── uploads/
├── logs/
└── docs/
```

| Service | Input | Output |
| --- | --- | --- |
| Command parser | commands.txt | Ordered typed commands with physical line numbers |
| Master loader | CSV paths | Validated channel/group records |
| Request validator | Request + masters | Validation result and reason |
| Request merger | Valid same-date requests | Merged requests + MERGED events |
| Priority scheduler | Requests | Priority/FIFO order |
| Channel allocator | Request + schedule snapshot | Tentative assignment or first failed slot |
| Adjacency checker | Candidate + slot assignments | Valid/invalid |
| Continuity manager | Previous channels + availability | Retained/additional channels |
| Pre-emption manager | Late request + lower-priority assignments | Tentative victim plan or no solution |
| Transaction coordinator | Tentative schedule changes | Atomic commit/rollback |
| Output writer | Committed schedule + logs | Exact official CSV files |

## 14. Localhost stack and setup

| Layer | Technology |
| --- | --- |
| Language | Python 3.10–3.12 |
| Web framework | Flask |
| Templates | Jinja2 |
| Frontend | HTML5, CSS3, JavaScript |
| Charts | Chart.js |
| Database | MySQL Community Server |
| ORM / migrations | SQLAlchemy / Flask-Migrate |
| Authentication | Flask-Login |
| Forms / CSRF | Flask-WTF |
| CSV | Python standard csv module |
| Optional exports | openpyxl (XLSX), ReportLab (PDF) |
| Testing | pytest |
| Runtime | Windows localhost, http://127.0.0.1:5000/ |

A compatible existing Python 3.10–3.12 installation may be used; do not require a new Python installation if a compatible interpreter is already present. Python 3.14 is outside the selected compatibility range.

- Use a project-local virtual environment.
- Read database credentials from environment variables; commit only .env.example.
- Never hardcode secrets or ask users to paste passwords into chat.
- Provide MySQL database creation instructions and a connection test.
- Provide migrations/initialisation, safe admin creation, sample loader and one documented run command.

Clean-install acceptance: create/activate venv → install pinned requirements → configure .env → create MySQL database → migrate/init → create admin → load masters/demo data → start Flask → open localhost → login and test workflow.

## 15. Import/export and reports

1. Admin uploads commands.txt and required master CSVs.
2. Validate extension, size, encoding and required headers.
3. Parse in physical line order; show preview and line-level diagnostics.
4. Admin confirms execution/import.
5. Run official command semantics and record batch hash/run history.
6. Generate exact three CSV outputs and make them downloadable.

Website-only XLSX/PDF/JSON exports may be offered separately. They must not alter the official evaluation CSV schemas.

| Report / metric | Definition |
| --- | --- |
| Daily allocation | Date, slot, channel, frequency, group, request |
| Daily utilisation | Unique committed channel-slot rows / 720 × 100 |
| Conflict log | Official reason, detail and processing order |
| Group/category summary | Request and allocation outcomes by group/category |
| Dashboard metrics | Real DB-backed counts for requests, allocations, conflicts and utilisation |

Do not count failed, tentative, rolled-back, channel-16 or pre-empted allocation rows in utilisation. Do not display fake values as live data.

## 16. Security

- Hash passwords; never store plaintext.
- Use a strong SECRET_KEY from .env.
- Enforce role and group scope on every protected server route.
- Use CSRF protection for state-changing forms.
- Use SQLAlchemy parameterized operations.
- Validate user input and uploaded files server-side.
- Protect login against repeated guessing.
- Store uploads outside public static directories with safe filenames and size limits.
- Never expose .env, passwords, secrets or debug tracebacks.
- Audit admin actions without logging secrets.
- Use transactions and schedule locks.
- Restrict backup/restore to admin with confirmation.
- Flask debug mode is development-only.

## 17. Tests and official planted scenarios

| Scenario from official README | Reference | Expected behaviour |
| --- | --- | --- |
| Exactly 8 slots | commands.txt line 118, REQ-0105 | Pass duration validation |
| 9 slots | line 121, REQ-0108 | DURATION_LIMIT |
| Only channels 14 and 15 available to different groups | lines 34 and 36 | 14 allocated; adjacent 15 unavailable to other group; whole request NO_CHANNEL |
| Same group requests 11 and 12 | line 28, REQ-0023 | Adjacent channels allowed |
| Late SECURITY with a free channel | lines 91–92 | Allocate without pre-emption |
| Late SECURITY when saturated | line 93, REQ-0083 | Pre-empt eligible Maintenance allocation; log PREEMPTED |
| Explicit channel 16 | line 128, REQ-0115 | RESERVED_CHANNEL |
| Continuity after clash | lines 37 and 45 | Move to channel 3 and keep it afterward where valid |
| Same-group overlapping requests | lines 74 and 87 | Union slots, maximum demand, earlier ID retained, later request MERGED |
| More than 3 channels | line 134 | TOO_MANY_CHANNELS |
| Unknown group | line 139 | UNKNOWN_GROUP |

The README line references count comments and blank physical lines. Verify line numbers against the unmodified commands.txt before writing tests.

- Unit tests: slot bounds, inclusive duration, channel range, fixed list validation, adjacency, same-group adjacency, multi-channel continuity, FIFO, priority, merge, first failed slot, rollback, late-only pre-emption and victim ordering.
- Integration tests: load actual official files, run commands end-to-end, verify filenames/headers/order, deterministic repeated runs and output formatting.
- Security tests: group isolation, admin-only endpoints, CSRF, concurrent schedule locking, safe imports and audit records.
- The README says expected output files are not supplied. Create reviewed expected results from the rules and planted cases; do not claim comparison with an unavailable expected file.

## 18. Development phases

| Phase | Work | Exit condition |
| --- | --- | --- |
| 0 | Inspect official ZIP and all files | Input contract and line numbers verified |
| 1 | Python environment, Flask skeleton, MySQL connection | Health route and DB connection pass |
| 2 | Models and migrations | Tables/relationships verified |
| 3 | Command parser and master loaders | Actual files parse correctly |
| 4 | Validation, merge, priority, allocator | Core unit tests pass |
| 5 | Continuity, late pre-emption, atomicity | Planted scenarios pass |
| 6 | Exact CSV output writer | Exact names, headers, order and values |
| 7 | Login, roles and group scope | Access tests pass |
| 8 | Request workflow and admin pages | Full submit/review lifecycle works |
| 9 | Schedule, conflicts, reports and dashboard | Real database-backed metrics |
| 10 | Import/export, audit and backup | Workflows complete |
| 11 | End-to-end and hidden-style tests | Deterministic and robust |
| 12 | Documentation and demo | Clean install and demo verified |

Build and verify the command-line evaluation engine early. Do not postpone it until after the dashboard; the allocation engine is the highest-risk project component.

## 19. Final deliverables

1. Complete Flask localhost website.
2. MySQL schema and migrations.
3. Official command parser and master CSV loaders.
4. Deterministic allocation engine.
5. Exact allocation_table.csv, utilisation.csv and conflict_log.csv generation.
6. Admin and group-user authentication and permissions.
7. Request submission, review and allocation workflow.
8. Schedule/timetable and conflict log pages.
9. Reports and dashboard.
10. Unit, integration, acceptance and security tests.
11. Demo-data loader that never overwrites official files.
12. .env.example and pinned requirements.txt.
13. Windows setup/run guide.
14. Project report diagrams and user manual.
15. Test report with passed, failed and not-yet-tested requirements.

## 20. Master prompt for another AI coding agent

You are the lead full-stack engineer for Team E037. Build the complete working application specified in this document for the project Campus Walkie-Talkie Channel and Time-Slot Allocation Engine. Team members: Surya Prakash.S and Sudarshan V.

Use Python 3.10–3.12, Flask, Jinja2, HTML/CSS/JavaScript, SQLAlchemy and MySQL. Run locally on Windows at http://127.0.0.1:5000/.

Read this specification and the actual official Team E037 sample ZIP before implementing the evaluator. The official README and command/output schemas take precedence. Do not invent missing input rows or expected outputs. Do not hardcode sample answers.

Implement parser, master loaders, validation, same-group merge, priority/FIFO, channel selection, adjacency, continuity, late-arrival-only pre-emption, all-or-nothing allocation, conflict logging and exact CSV outputs first. Then integrate the same domain services with the Flask website.

Preserve inclusive slots, fixed-channel exactness, official reason codes, processing order, victim selection, whole-victim removal, no victim retry, output filenames, header order, sorting and utilisation formula.

Build a complete authenticated admin/group-user website with functional pages and database-backed metrics. Enforce permissions server-side. Include migrations, seed scripts, tests, safe uploads, CSRF, password hashing, backups and setup documentation.

Work in small verifiable milestones. After each phase, run tests and report exact files changed, commands run, results, known gaps and next step. Never claim a feature or test is complete unless implemented and verified. No placeholder buttons or fake live data.

## 21. Open items to verify from the actual ZIP

1. Verify actual filenames, encoding, delimiters and all CSV rows.
2. Verify physical line numbers in unmodified commands.txt.
3. Check for any additional college clarification.
4. Confirm exact decimal formatting and line-ending expectations if evaluator is byte-sensitive.
5. Confirm whether the earlier two-site website extension remains required; the inspected official README and command schema do not include a site field.
6. Confirm how website emergency requests should be represented internally; official REQUEST syntax has no emergency fields.

Until verified, do not invent answers. Keep the official evaluator path exact and isolate optional website extensions from it.

---

**End of master specification — Team E037**