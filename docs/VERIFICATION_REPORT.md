# Verification Report

**Project:** E037-ECE-018 — Campus Walkie-Talkie Channel and Time-Slot Allocation Engine  
**Verification date:** 24 November 2026  
**Scope:** Uploaded source ZIP, before publication of this cleaned package.

## Results

| Check | Result | Evidence |
|---|---|---|
| Python syntax compilation | PASS | All 14 Python source files compiled. |
| Jinja template parsing | PASS | All 21 HTML templates parsed without syntax errors. |
| Automated test suite | PASS | `python -m pytest -q` — 9 passed. |
| Official sample-pack command runner | PASS | 16 channels, 15 groups, 128 requests, 356 allocation rows, 11 conflict records, 0 parser diagnostics. |
| Output CSV files | PASS | All three expected CSV files were generated. |
| Template endpoint references | PASS | All template `url_for('main.…')` references matched route function names. |
| Live Flask startup and browser workflow | NOT RUN | Flask and its Flask extensions are not installed in this verification environment. |
| Live MySQL connection | NOT RUN | No configured MySQL service or credentials were supplied. |

## Official sample-pack run

The standalone runner completed successfully against the supplied official sample files:

- `allocation_table.csv`
- `utilisation.csv`
- `conflict_log.csv`

Observed dates: 2026-10-12 through 2026-10-14. The runner reported no command diagnostics.

## Important limitations

- The nine automated tests cover the supplied official command pack, key allocation constraints, output headers, deterministic output, and malformed command diagnostics. They are the tests present in the supplied project; this report does not claim exhaustive coverage of every browser workflow.
- A live website session, form submissions, authentication workflow, and database integration must still be checked on the target Windows computer after installing dependencies.
- A live MySQL connection was not tested. The default local configuration uses SQLite.
- The official sample pack does not include a separate expected-output fixture, so no independent golden-file comparison is claimed.

## Local verification on Windows

From the project root:

```powershell
setup_windows.bat
run_windows.bat
```

Open `http://127.0.0.1:5000` and test login, admin and group-user workflows, request submission, allocation runs, schedules, conflicts, reports and CSV downloads.

Then run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\run_official.py
```

Do not mark the live website or MySQL checks as passed until they have actually been run.
