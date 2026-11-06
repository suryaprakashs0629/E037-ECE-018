# Campus Walkie-Talkie Channel and Time-Slot Allocation Engine

**Team ID:** E037
**Team members:** Surya Prakash.S; Sudarshan V.
**Release:** Localhost multi-page Flask application + official Team E037 evaluation runner

This is a software simulation and management system. It does not transmit radio signals or control physical walkie-talkies.

## Product and visual direction

The website has separate administrator and group-user navigation, a persistent left sidebar, a light workspace, restrained navy/charcoal and blue colours, readable tables, compact operational cards and a 48-slot timetable. It deliberately avoids purple gradients, neon glows, oversized marketing hero sections, fake charts and placeholder controls.

## Functional areas

### Administrator workspace
- Operations dashboard with database-backed request, allocation, conflict and utilisation metrics.
- Request management: filter, review, approve, reject with a reason, and perform permitted edits.
- Allocation runs: select a date, run the engine, and view allocated, failed and pre-empted outcomes.
- 48-slot allocation schedule and channel plan (1–16, with channel 16 reserved).
- Group directory and user account administration.
- Conflict log, reports, official CSV export, command-file lab, notifications and audit trail.

### Group-user workspace
- Separate group-user dashboard and navigation.
- Submit and monitor requests for the assigned group only.
- Edit own group's pending requests.
- View own group's allocations/schedule and notifications.
- No access to other groups' request data or administrator actions.

### Official Team E037 command engine
- Reads the original `commands.txt` from top to bottom and retains physical line numbers.
- Loads the official `channels.csv` and `groups.csv` files.
- Supports `LOAD_CHANNELS`, `LOAD_GROUPS`, `REQUEST`, `ALLOCATE`, `PRINT_TABLE`, `PRINT_UTILISATION` and `PRINT_CONFLICTS`.
- Uses inclusive slot numbers 1–48 (`duration = end_slot - start_slot + 1`).
- Applies category priority and FIFO for the initial `ALLOCATE` command.
- Merges overlapping same-group requests before initial allocation, using the union of slots and maximum simultaneous channel demand.
- Enforces channel 16 reservation, same-channel exclusivity, cross-group adjacency, exact fixed-channel lists, continuity and all-or-nothing allocation.
- Allows late-arrival pre-emption only for `REQUEST` commands after that date's `ALLOCATE`; a selected victim is removed as a whole and is not retried.
- Writes the exact official evaluation files and column order: `allocation_table.csv`, `utilisation.csv` and `conflict_log.csv`.

## Radio and scheduling rules

| Item | Rule |
|---|---|
| Total channels | 16 |
| Allocatable channels | 1–15 |
| Reserved channel | 16; never allocated |
| Starting frequency | 446.00625 MHz |
| Spacing | 12.5 kHz |
| Slots per day | 48 |
| Slot duration | 30 minutes |
| Slot numbering | 1–48, inclusive |
| Maximum request duration | 8 consecutive slots |
| Maximum channels per request | 3 |
| Priority | SECURITY → MEDICAL → EVENTS → MAINTENANCE |
| Same-priority order | FIFO |

Different groups at the same slot cannot use the same or adjacent channel numbers. The same group may use adjacent channels. The official command interface is the single-schedule format defined by the E037 README; the website does not invent a site column that is absent from that contract.

## Requirements

- Windows 10/11
- Python 3.10–3.12 (project baseline)
- MySQL Community Server
- VS Code or another Python editor

Python 3.14 is outside the version range selected in the project specification. Use Python 3.12 for the documented setup.

## Windows setup — MySQL configuration

### 1. Extract and open the project

Extract the ZIP to a path such as `D:\Projects\Campus_Walkie_Talkie_E037` and open that folder in VS Code. Use **Terminal → New Terminal** and select PowerShell.

### 2. Create the Python environment and install packages

Run the setup helper:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup_windows.ps1
```

The script creates `.venv`, installs `requirements.txt`, and copies `.env.example` to `.env` if it does not already exist. If Python 3.12 is missing, install Python 3.12 x64 and run the script again.

### 3. Create the MySQL database and local application user

Start your MySQL Community Server service. In MySQL Workbench, connect to your local server and execute the following SQL. Choose your own strong password:

```sql
CREATE DATABASE campus_radio_manager
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER 'campus_app'@'127.0.0.1' IDENTIFIED BY 'CHOOSE_A_STRONG_PASSWORD';
GRANT ALL PRIVILEGES ON campus_radio_manager.* TO 'campus_app'@'127.0.0.1';
FLUSH PRIVILEGES;
```

### 4. Configure `.env`

Open `.env` in VS Code. Set `DATABASE_URL` to your database connection and replace `SECRET_KEY` with a generated secret. URL-encode special characters in the database password if necessary.

```ini
DATABASE_URL=mysql+pymysql://campus_app:YOUR_PASSWORD@127.0.0.1:3306/campus_radio_manager?charset=utf8mb4
SECRET_KEY=paste-a-long-random-value-here
FLASK_DEBUG=1
```

Generate a secret with:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

Do not share `.env` or commit it to Git.

### 5. Initialise the database and load the official master data

```powershell
.\.venv\Scripts\python.exe scripts\init_db.py
```

This creates the application tables and loads the 16 official channels and 15 official groups. For a migration-managed setup, see `docs/MIGRATIONS.md` instead; do not initialise the same empty database using both methods.

### 6. Create the first administrator

```powershell
.\.venv\Scripts\python.exe scripts\create_admin.py
```

Enter the administrator username, full name and password when prompted. The password is hashed and is not written to source files. After signing in, use **User accounts** to create group-user accounts for the registered groups.

### 7. Start the website

```powershell
.\.venv\Scripts\python.exe run.py
```

Open `http://127.0.0.1:5000/` and sign in using the administrator account you created.

Health checks:
- `http://127.0.0.1:5000/health`
- `http://127.0.0.1:5000/health/db`

`start_app.bat` is also included; it starts the app using the already-created `.venv`.

## Run the official sample independently of the website

The command-line runner does not require Flask login or MySQL. It exercises the same framework-independent allocation engine used by the website:

```powershell
.\.venv\Scripts\python.exe scripts\run_official.py
```

Default output folder: `exports/official_run/`, containing the three official CSV files. To process another copy of the official files:

```powershell
.\.venv\Scripts\python.exe scripts\run_official.py --commands "D:\path\commands.txt" --channels "D:\path\channels.csv" --groups "D:\path\groups.csv" --output "D:\path\output"
```

Do not edit the bundled official sample files in place. The web Command File Lab copies them into a unique batch directory before running.

## Tests and verification

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The tests cover official sample-pack processing, exact output headers, planted scenarios, inclusive duration, channel-16 rejection, all-or-nothing allocation, utilisation, deterministic outputs, duplicate request IDs and invalid dates.

The official README says expected output files are not supplied with the sample pack. The included tests assert the planted cases and file contract; they do not claim a field-for-field comparison to an unavailable college expected-output file.

## Scope notes

- The official command format has no site field. The evaluator therefore follows the provided single-schedule contract and does not invent site IDs or output columns.
- Earlier website discussion considered two sites, but the official E037 README/command schema does not define a site column. A site-aware website extension should only be added after the team/college confirms how sites are represented.
- Emergency submission is a website-only extension controlled by an admin account permission. It requires justification and receives SECURITY-level priority. It never permits channel 16. The official `REQUEST` command syntax is unchanged.
- The Flask development server is for local demonstration only, not production hosting.

## Verification limitation

The build environment used to create this ZIP did not have Flask/Flask-SQLAlchemy/Flask-Login/Flask-WTF/Flask-Migrate/PyMySQL installed, and it could not reach the package index to install them. The standalone allocator, test suite, Python syntax and Jinja template parsing were verified; a live Flask + MySQL browser session was not run in that environment. Complete the Windows setup above and check `/health` and `/health/db` before your demo.

## Team

**Team ID:** E037
**Surya Prakash.S**
**Sudarshan V**
