<div align="center">

# 📡 Campus Walkie-Talkie Channel & Time-Slot Allocation Engine

### A browser-based campus communication scheduling and channel-allocation system

**Team E037 · Project ECE-018**

[![Python](https://img.shields.io/badge/Python-3.10--3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/Database-SQLite%20%7C%20MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://www.sqlite.org/)

<br />

[**Open the GitHub Repository**](https://github.com/suryaprakashs0629/E037-ECE-018)

</div>

---

## Welcome

This README is a step-by-step guide for anyone opening this project for the first time. Follow the instructions in order to install the application on a Windows computer and use it through a local web browser.

> [!TIP]
> **Quick start:** Download the project → install Python → run `setup_windows.bat` once → run `run_windows.bat` → open `http://127.0.0.1:5000` in your browser.

---

<details>
<summary><b>📑 Table of Contents</b></summary>

1. [Run the Project Locally](#1-run-the-project-locally)
   - [1.1 Requirements](#11-requirements)
   - [1.2 Download the project](#12-download-the-project)
   - [1.3 Open the correct folder](#13-open-the-correct-folder)
   - [1.4 First-time setup (run once)](#14-first-time-setup-run-once)
   - [1.5 Start the application](#15-start-the-application)
   - [1.6 Open the website in your browser](#16-open-the-website-in-your-browser)
   - [1.7 Stop the application](#17-stop-the-application)
2. [First-Time User Guide](#2-first-time-user-guide)
3. [Project Overview](#3-project-overview)
4. [Allocation Rules](#4-allocation-rules)
5. [Run the Official Command-Line Evaluation](#5-run-the-official-command-line-evaluation)
6. [Run the Automated Tests](#6-run-the-automated-tests)
7. [Project Structure](#7-project-structure)
8. [Database Information](#8-database-information)
9. [Troubleshooting](#9-troubleshooting)
10. [Security and Usage Notes](#10-security-and-usage-notes)
11. [Team Information](#11-team-information)

</details>

---

# 1. Run the Project Locally

## 1.1 Requirements

Before you begin, make sure you have:

| Requirement | Details |
| :--- | :--- |
| **Operating system** | Windows 10 or Windows 11 |
| **Python** | Python 3.10–3.12; 64-bit recommended |
| **Browser** | Chrome, Edge, Firefox, or another modern browser |
| **Internet** | Required for the first-time package installation |
| **Git** | Optional; only needed if you clone the repository |

> [!NOTE]
> **You do not need to install MySQL for the default local setup.** The application uses SQLite unless you configure another database.

### Install Python

1. Visit https://www.python.org/downloads/.
2. Download and install Python 3.10, 3.11, or 3.12.
3. If the installer offers **Add Python to PATH**, enable it.
4. Complete the installation.
5. Open PowerShell and check Python:

```powershell
py --version
```

If `py` is not recognised, restart PowerShell. If it still fails, repair or reinstall Python and enable the Python Launcher/PATH options.

---

## 1.2 Download the project

### Option A — Download ZIP (easiest)

1. Open the [E037-ECE-018 GitHub repository](https://github.com/suryaprakashs0629/E037-ECE-018).
2. Click the green **Code** button.
3. Select **Download ZIP**.
4. When the download finishes, right-click the ZIP file and choose **Extract All**.
5. Open the extracted project folder.

### Option B — Clone with Git

If Git is installed, open PowerShell in the location where you want the project and run:

```powershell
git clone [https://github.com/suryaprakashs0629/E037-ECE-018.git](https://github.com/suryaprakashs0629/E037-ECE-018.git)
cd E037-ECE-018
```

---

## 1.3 Open the correct folder

Open the main project folder. You should be able to see these files:

```text
E037-ECE-018/
├── app/
├── docs/
├── migrations/
├── sample_data/
├── scripts/
├── tests/
├── config.py
├── requirements.txt
├── run.py
├── setup_windows.bat
└── run_windows.bat
```

> [!IMPORTANT]
> **Important:** Run the `.bat` files from the folder that contains them. If you cannot see `setup_windows.bat`, you have not opened the correct folder yet.

---

## 1.4 First-time setup (run once)

1. Open the main project folder in File Explorer.
2. Find **`setup_windows.bat`**.
3. Double-click it.
4. A terminal window will open. Allow the setup process to run.
5. Follow any prompts shown in the terminal. If it asks you to create the first administrator account, enter the requested details.
6. Wait until the script reports that setup has completed.
7. If an error appears, stop here and use the [Troubleshooting](#9-troubleshooting) section.

The setup script prepares the local Python environment, installs the required packages, and initialises the local application database.

> [!WARNING]
> You normally need to run this setup only once for each local installation. Keep your administrator credentials safe. Never upload your `.env` file, password, or local database to GitHub.

---

## 1.5 Start the application

Whenever you want to use the website:

1. Open the main project folder.
2. Double-click **`run_windows.bat`**.
3. Keep the terminal window open.
4. Wait until Flask displays a message showing that the server is running. The address should look like:

```text
[http://127.0.0.1:5000](http://127.0.0.1:5000)
```

---

## 1.6 Open the website in your browser

1. Open Chrome, Edge, Firefox, or another browser.
2. Enter this address:
   **`http://127.0.0.1:5000`**
3. The project login page should appear.
4. Sign in using the administrator credentials created during setup.

You are now using the application locally.

> [!IMPORTANT]
> **Keep the terminal open while using the website.** Closing it stops the local server. The address `127.0.0.1` refers to your own computer; it is not a public website URL.

---

## 1.7 Stop the application

1. Return to the terminal window running Flask.
2. Press <kbd>Ctrl</kbd> + <kbd>C</kbd>.
3. Wait for the server to stop.
4. You can then close the terminal.

---

# 2. First-Time User Guide

The pages available to you depend on your account role.

### 🛡️ Administrator

An administrator can manage groups and users, review channel requests, approve or reject requests, run channel allocations, view schedules, inspect conflicts, and access reports.

### 👥 Group user

A group user can sign in with the account assigned to them, submit channel requests, check request status, and view relevant group schedules and notifications.

### Suggested project demonstration

For a short walkthrough:

1. Sign in as administrator.
2. Open the dashboard and review its summary.
3. Open the group and user management pages.
4. Review the available channel requests.
5. Approve an eligible request if required by the workflow.
6. Run the allocation process.
7. Open the allocation schedule.
8. Inspect the conflict log and reports.

Use the supplied sample data and follow the application's validation messages. A request should not be assumed to be allocatable if it violates a scheduling rule.

---

# 3. Project Overview

The Campus Walkie-Talkie Channel and Time-Slot Allocation Engine is a software application that simulates communication-channel scheduling among campus departments or user groups.

It manages allocation requests, applies scheduling constraints, detects conflicts, and presents allocation results through a browser-based interface.

> [!NOTE]
> **This project is a software simulation. It does not transmit radio signals, communicate with physical walkie-talkies, or configure real radio hardware.**

## Main features

- Administrator and group-user access.
- Group and user management.
- Channel allocation request submission and review.
- Automatic channel and time-slot allocation.
- Daily allocation schedule.
- Conflict logging.
- Utilisation and reporting views.
- CSV output generation.
- Official Team E037 command-file runner.
- Automated tests for core allocation behaviour.

## Technology stack

| Layer | Technology |
| :--- | :--- |
| **Programming language** | Python |
| **Backend** | Flask |
| **Frontend** | HTML, CSS, JavaScript |
| **ORM** | Flask-SQLAlchemy |
| **Default local database** | SQLite |
| **Optional database** | MySQL |
| **Automated tests** | Pytest |

---

# 4. Allocation Rules

| Parameter | Rule |
| :--- | :--- |
| **Total channel numbers** | `16` |
| **Allocatable channels** | `1–15` |
| **Reserved channel** | `16` |
| **Starting frequency** | `446.00625 MHz` |
| **Channel spacing** | `12.5 kHz` |
| **Slots per day** | `48` |
| **Duration per slot** | `30 minutes` |
| **Maximum consecutive slots per request** | `8` |
| **Maximum channels per group per slot** | `3` |
| **Priority order** | `SECURITY → MEDICAL → EVENTS → MAINTENANCE` |

**Other important rules:**

- Channel 16 is reserved and must not be allocated.
- Different groups must not receive the same or adjacent channel numbers in the same time slot.
- Requests are processed according to priority and the applicable ordering rules.
- Allocations must satisfy the all-or-nothing requirement.
- Emergency handling is subject to authorisation and justification rules.

See the files in `docs/` for the project's detailed design and implementation decisions.

---

# 5. Run the Official Command-Line Evaluation

The repository includes a command-line runner and sample input files for Team E037.

1. Complete the initial setup in Section 1.
2. Open the main project folder.
3. Double-click **`run_official_windows.bat`**.
4. Wait for the command-line run to finish.
5. Inspect the generated files in:

```text
exports/official_run/
```

The expected output filenames are:

- `allocation_table.csv`
- `utilisation.csv`
- `conflict_log.csv`

The official sample inputs are stored in:

```text
sample_data/team_e037/
```

> [!CAUTION]
> **Do not overwrite or edit the original supplied sample files during an evaluation.** Make a separate copy if you want to experiment with modified inputs.

---

# 6. Run the Automated Tests

After setup, open PowerShell in the main project folder and run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Pytest will execute the tests in the `tests/` directory and display a summary.

If pytest is unavailable, rerun `setup_windows.bat` and check that setup completes successfully.

---

# 7. Project Structure

```text
E037-ECE-018/
│
├── app/                     # Flask application, routes, services and templates
├── docs/                    # Architecture, design and project documentation
├── migrations/              # Database migration files
├── sample_data/             # Official Team E037 sample inputs
├── scripts/                 # Setup, database and command-line scripts
├── tests/                   # Automated tests
├── exports/                 # Generated evaluation outputs
├── logs/                    # Runtime logs
├── uploads/                 # Runtime upload directory
│
├── .env.example             # Example environment configuration
├── .gitignore               # Files excluded from Git
├── config.py                # Application configuration
├── requirements.txt         # Python dependencies
├── requirements-dev.txt     # Development/test dependencies
├── run.py                   # Application entry point
├── setup_windows.bat        # First-time Windows setup
├── run_windows.bat          # Starts the local web application
├── run_official_windows.bat # Runs official command-line evaluation
├── START_HERE.txt           # Short starting guide
└── VERSION.txt              # Project version
```

The `.venv/`, `.env`, and local database are created or used on the local computer and should not be committed to the public repository.

---

# 8. Database Information

The default local setup uses SQLite. This avoids the need to install and run a separate database server for a basic demonstration.

The project also includes MySQL support for environments where a MySQL database is configured.

For a normal first-time evaluation, use the default setup. Do not change the database configuration unless instructed by the project team.

> [!WARNING]
> **Do not delete the local database while the application is in use.** It may contain administrator accounts, users, requests, and allocation records.

---

# 9. Troubleshooting

<details open>
<summary><b>Python or <code>py</code> is not recognised</b></summary>
<br />

- Install Python 3.10–3.12 from [python.org](https://www.python.org/downloads/).
- Enable the Python Launcher and PATH options if offered.
- Close and reopen PowerShell.
- Check again using `py --version`.

</details>

<details>
<summary><b>The setup window closes or reports an error</b></summary>
<br />

- Run `setup_windows.bat` from the main project folder.
- Check that Python is installed.
- Check your internet connection.
- Read the error shown in the terminal.

If the problem continues, copy the complete error message before asking for help.

</details>

<details>
<summary><b>The browser says the site cannot be reached</b></summary>
<br />

- Confirm that `run_windows.bat` is running.
- Check that the terminal displays the local Flask address.
- Keep the terminal open.
- Enter `http://127.0.0.1:5000` exactly.
- If port 5000 is already in use, stop the other application using it or contact the project team.

</details>

<details>
<summary><b>Administrator login does not work</b></summary>
<br />

- Use the credentials created during initial setup.
- Check that Caps Lock is off.
- Do not delete the database to try to fix a login problem.
- Contact the project team if the account or database needs recovery.

</details>

<details>
<summary><b>Python package or import errors appear</b></summary>
<br />

Run the setup script again and allow it to finish. If the issue continues, share the complete terminal error with the project team.

</details>

---

# 10. Security and Usage Notes

- Never publish passwords, secret keys, `.env` files, or private database files.
- Do not share administrator credentials.
- The Flask development server is intended for local development and demonstration, not production deployment.
- The local browser address is intended for use on the computer running the application.
- Use authorised accounts and the supplied sample data.
- Back up the local database before changing or deleting it.

---

# 11. Team Information

| Field | Details |
| :--- | :--- |
| **Project code** | ECE-018 |
| **Team ID** | E037 |
| **Project title** | Campus Walkie-Talkie Channel and Time-Slot Allocation Engine |
| **Team members** | • Surya Prakash S<br>• Sudarshan V |
| **GitHub repository** | https://github.com/suryaprakashs0629/E037-ECE-018 |

---

<div align="center">

**Team E037 · ECE-018**

*Campus Walkie-Talkie Channel and Time-Slot Allocation Engine*

</div>
