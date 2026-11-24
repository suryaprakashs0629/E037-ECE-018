# ECE-018 – Campus Walkie-Talkie Channel and Time-Slot Allocation Engine — Sample Data Pack
Prepared by 10 SECONDS for Team E037.

This pack is the input for a campus walkie-talkie allocation engine: 16 UHF channels (12.5 kHz spacing from 446.00625 MHz, channel 16 reserved for emergencies), 15 user groups in 4 categories, and three days of requests (2026-10-12 to 2026-10-14). Your engine reads `commands.txt` and prints, per day, the allocation table, the utilisation summary, and finally the conflict log.

Slots: the day is split into 48 half-hour slots; slot n starts at (n−1) × 30 minutes after 00:00 (slot 1 = 00:00–00:30, slot 13 = 06:00–06:30, slot 48 = 23:30–24:00). A request covers start_slot to end_slot inclusive; its duration is end_slot − start_slot + 1 slots.

Pack conventions where the brief is silent: REQUEST lines before a day's ALLOCATE command are that day's submitted requests, in submission order. ALLOCATE first validates (unknown group, more than 8 slots, more than 3 channels, explicit channel 16), then merges overlapping requests of the same group (union of the slots, the larger channel count, kept under the earlier request id), then allocates in priority order (SECURITY, MEDICAL, EVENTS, MAINTENANCE) and submission order. REQUEST lines AFTER that day's ALLOCATE are late arrivals and are allocated immediately; only a late request may pre-empt. When it pre-empts, it removes the whole allocation of one lower-priority request (lowest category first, then the latest submitted) that overlaps its slots, provided that this makes the late request fit; the pre-empted request is not retried. For multi-channel requests, a slot keeps the channels the request held in the previous slot where still valid, then adds the lowest valid channels. `fixed_channels` = ANY lets the engine choose; a list of channel numbers means exactly those channels in every slot of the request. Utilisation counts allocatable channel-slots: 15 channels × 48 slots = 720 per day.

## Files
| File | What it holds | Rows |
|---|---|---|
| channels.csv | Channel plan (1–16) | 16 |
| groups.csv | User groups with category and priority | 15 |
| commands.txt | Requests, ALLOCATE and print commands for three days | 140 |

## Column reference
Conventions: dates `YYYY-MM-DD`; timestamps `YYYY-MM-DD HH:MM:SS` (24h, IST, no timezone suffix); money in Rs as plain decimals (no commas, no symbol); percentages as plain numbers (12.5 = 12.5%); booleans `true`/`false`; IDs uppercase with a fixed prefix.

### channels.csv
| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| channel_no | integer | - | 1–16 | Primary key; 16 is never allocated |
| frequency_mhz | decimal | MHz, 5 dp | 446.00625 + (channel_no − 1) × 0.0125 | Neighbouring channels are 12.5 kHz apart (differ by 1) |
| spacing_khz | decimal | kHz | 12.5 |  |
| is_emergency | boolean | true/false | true only for 16 |  |

### groups.csv
| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| group_id | string | GRP-nn | GRP-01 … GRP-15 | Primary key |
| group_name | string | - |  |  |
| category | string | - | SECURITY, MEDICAL, EVENTS, MAINTENANCE |  |
| priority_rank | integer | - | 1 (highest) – 4 | SECURITY 1, MEDICAL 2, EVENTS 3, MAINTENANCE 4 |
| contact_name | string | - |  | Not used by any rule |
| contact_mobile | string | 10 digits | starts 6–9 | Not used by any rule |

## Command file format
`commands.txt` holds one command per line as `COMMAND_NAME|arg1|arg2|...`. Commands must be processed in file order, top to bottom. Lines starting with `#` are comments and blank lines are ignored.

| Command | Arguments (in order) | Meaning |
|---|---|---|
| LOAD_CHANNELS | file | Load channels.csv |
| LOAD_GROUPS | file | Load groups.csv |
| REQUEST | request_id \| group_id \| date \| start_slot \| end_slot \| channels_needed \| fixed_channels | Submit a request (REQ-nnnn). fixed_channels is ANY or semicolon-separated channel numbers |
| ALLOCATE | YYYY-MM-DD | Validate, merge and allocate all requests submitted so far for that date |
| PRINT_TABLE | YYYY-MM-DD | Print the per-slot allocation table for the date |
| PRINT_UTILISATION | YYYY-MM-DD | Print the utilisation summary for the date |
| PRINT_CONFLICTS | ALL | Print the conflict log for all days |

`slot_start` is HH:MM. `utilisation_pct` = used / 720 × 100, rounded to 2 decimals. `reason` is one of UNKNOWN_GROUP, DURATION_LIMIT, TOO_MANY_CHANNELS, RESERVED_CHANNEL, MERGED, NO_CHANNEL, PREEMPTED. `detail` is `NONE` except: MERGED → the request id it was merged into; PREEMPTED → the request id that pre-empted it; NO_CHANNEL → the first slot number that could not be served.

## Planted scenarios
Line numbers count the header row as line 1, so the first data row of a CSV is line 2. For commands.txt the line number is the physical line in the file (comment lines included).

- **Request for exactly 8 slots versus 9** — commands.txt line 118 (REQ-0105, GRP-01 SECURITY, 2026-10-14 slots 18–25) spans exactly 8 slots → accepted. commands.txt line 121 (REQ-0108, GRP-02 SECURITY, 2026-10-14 slots 18–26) spans 9 slots → rejected with DURATION_LIMIT.
- **Only channels 14 and 15 free, requested by two different groups (adjacent, second rejected)** — On 2026-10-12, slots 34–35 (16:30–17:30): seven requests in priority order take channels 1, 3, 5, 7, 9, 11+12 and then 14 (commands.txt line 34 (REQ-0029, GRP-10 EVENTS, 2026-10-12 slots 34–35) gets 14, because 13 touches 12). Only 14 and 15 were usable; commands.txt line 36 (REQ-0031, GRP-13 MAINTENANCE, 2026-10-12 slots 32–35) (lower priority, 1 channel) would need 15, which is next to 14 held by another group, and 16 is reserved → NO_CHANNEL for the whole request (its first two slots were free, but partial allocations are not kept).
- **Same group needing 2 channels (adjacent allowed)** — commands.txt line 28 (REQ-0023, GRP-09 EVENTS, 2026-10-12 slots 34–35) needs 2 channels and gets 11 and 12 — adjacent channels inside the same group are allowed.
- **MAINTENANCE allocated first by time, then SECURITY request arrives for the same slots** — commands.txt line 51 (REQ-0042, GRP-14 MAINTENANCE, 2026-10-13 slots 30–33) (MAINTENANCE) is allocated by the ALLOCATE at line 91; commands.txt line 92 (REQ-0082, GRP-01 SECURITY, 2026-10-13 slots 30–33) (SECURITY) arrives after it for the same slots and still finds a free channel → no pre-emption. Then slots 20–21 (09:30–10:30) on the same day is saturated (channels 1, 3, 5, 7, 9+10, 12, 14 held; MAINTENANCE GRP-15 holds 14 via commands.txt line 71 (REQ-0062, GRP-15 MAINTENANCE, 2026-10-13 slots 20–21)); the late SECURITY request commands.txt line 93 (REQ-0083, GRP-03 SECURITY, 2026-10-13 slots 20–21) finds no channel, so it pre-empts the MAINTENANCE allocation (logged PREEMPTED) and takes channel 14.
- **Request including channel 16 explicitly (rejected)** — commands.txt line 128 (REQ-0115, GRP-06 MEDICAL, 2026-10-14 slots 33–35) asks explicitly for channel 16 (the emergency channel) → rejected. Compare commands.txt line 129 (REQ-0116, GRP-07 MEDICAL, 2026-10-14 slots 33–35), which asks for channel 6 and gets it.

Extra traps (realistic things your validation should catch):

- **Continuity after a clash** — commands.txt line 37 (REQ-0032, GRP-11 EVENTS, 2026-10-12 slots 24–29) starts on channel 1, but commands.txt line 45 (REQ-0040, GRP-01 SECURITY, 2026-10-12 slots 26–27) (SECURITY, processed first) holds channel 1 in slots 26–27; the EVENTS request moves to the lowest valid channel 3 there and then KEEPS channel 3 for the rest of its slots (it does not jump back to 1).
- **Overlapping requests from one group** — commands.txt line 74 (REQ-0065, GRP-06 MEDICAL, 2026-10-13 slots 35–38) and commands.txt line 87 (REQ-0078, GRP-06 MEDICAL, 2026-10-13 slots 37–40) come from the same group and overlap → merged into one request covering slots 35–40 (kept under the first request id; the second is logged MERGED).
- **More than 3 channels** — commands.txt line 134 (REQ-0121, GRP-12 EVENTS, 2026-10-14 slots 40–42) asks for 4 channels in each slot → rejected (a group may hold at most 3 channels in one slot).
- **Unknown group** — commands.txt line 139 (REQ-0126, GRP-21 unregistered, 2026-10-14 slots 40–42) names GRP-21, which is not in groups.csv → rejected.

## What is NOT in this pack
Expected outputs are not provided for this set. Validate your engine with your own test suite against the rules in your brief (BR-01 … BR-07). A separate hidden input set with the same schema will be used at final evaluation; outputs are compared field-for-field, so follow the column formats above exactly in your own output.

## Output format expected at evaluation
Produce these files (CSV, header row, same conventions as above). Column order matters.

### allocation_table.csv
One row per allocated channel per slot, ordered by date, slot, channel_no.

Columns in order: `date`, `slot`, `slot_start`, `channel_no`, `frequency_mhz`, `group_id`, `request_id`

### utilisation.csv
One row per day.

Columns in order: `date`, `channel_slots_used`, `channel_slots_available`, `utilisation_pct`

### conflict_log.csv
One row per rejected, merged or pre-empted request, in processing order.

Columns in order: `date`, `request_id`, `group_id`, `reason`, `detail`
