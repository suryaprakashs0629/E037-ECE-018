# Team E037 build verification report

This report records checks performed on the packaged source before delivery.

## Automated checks

- Python syntax compilation: passed for application, scripts, run.py and configuration.
- Jinja template compilation: passed for all 21 HTML templates.
- Pytest: 9 tests passed.
- Official command runner: completed with 0 command diagnostics.

## Official sample-pack run observed in this environment

| Measure | Result |
|---|---:|
| Channels loaded | 16 |
| Groups loaded | 15 |
| Requests submitted | 128 |
| Allocation rows | 356 |
| Conflict records | 11 |
| Dates | 2026-10-12 to 2026-10-14 |
| Parser diagnostics | 0 |

The output folder produced the expected three files and exact header sequences. The conflict reason totals were: 5 `NO_CHANNEL`, 1 `MERGED`, 1 `PREEMPTED`, 1 `DURATION_LIMIT`, 1 `RESERVED_CHANNEL`, 1 `TOO_MANY_CHANNELS`, and 1 `UNKNOWN_GROUP`.

## Checks not performed in this build environment

The current build environment did not have Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF or PyMySQL installed, and package download access was unavailable. Therefore a live Flask server, browser-rendered route workflow and live MySQL connection could not be executed here. The source includes the pinned dependencies and setup scripts; run the included Windows setup and health checks on the target laptop before treating the complete website runtime as verified.

The college did not provide expected-output CSV files in the sample pack README, so no comparison against an external expected-output fixture is claimed.
- Template endpoint scan: all 27 distinct `url_for('main.…')` references found in templates match route function names.
