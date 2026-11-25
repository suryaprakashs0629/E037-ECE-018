<div align="center">

# 📡 Campus Walkie-Talkie Channel & Time-Slot Allocation Engine

### A simple web application for managing campus walkie-talkie channel requests and schedules

**Team E037 · Project ECE-018**

[![Python](https://img.shields.io/badge/Python-3.10--3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/Database-SQLite%20%7C%20MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://www.sqlite.org/)

<br />

## 🎬 Watch the 5-Minute Project Demo

[**▶ CLICK HERE TO WATCH THE PROJECT DEMONSTRATION**](https://drive.google.com/file/d/1qOfa2fZmvCGuA6lPnt4pChtag2y3cLoY/view?usp=sharing)

See the dashboard, user accounts, channel requests, automatic allocation, schedules and reports.

[**View GitHub Repository**](https://github.com/suryaprakashs0629/E037-ECE-018)

</div>

---

## 👋 Welcome

This project helps campus teams manage walkie-talkie channel requests and time slots through a web-based dashboard.

You can run the application on a Windows computer using the simple steps below. **You do not need to know programming to start the application.**

## 🚀 Run the Project on Your Computer

Follow these steps in order.

### Before you start

Make sure you have:

- A Windows 10 or Windows 11 computer.
- An internet connection for the first-time setup.
- Python **3.10, 3.11 or 3.12** installed.

> **No MySQL installation is required** for the normal setup. The application uses a local SQLite database by default.

### Step 1 — Download the project

1. Open the [GitHub project page](https://github.com/suryaprakashs0629/E037-ECE-018).
2. Click the green **Code** button.
3. Select **Download ZIP**.
4. After downloading, right-click the ZIP file and choose **Extract All**.

### Step 2 — Install Python

1. Visit [https://www.python.org/downloads/](https://www.python.org/downloads/).
2. Download Python 3.10, 3.11 or 3.12.
3. Start the installer.
4. Select **Add Python to PATH** if the option is shown.
5. Complete the installation.

If Python is already installed in a supported version, you can continue to the next step.

### Step 3 — Open the project folder

Open the extracted **E037-ECE-018** folder.

You should see files such as:

```text
E037-ECE-018/
├── app/
├── docs/
├── scripts/
├── tests/
├── setup_windows.bat
└── run_windows.bat
```

Make sure you are inside the folder that contains the two `.bat` files.

### Step 4 — Set up the project (first time only)

1. Find **`setup_windows.bat`**.
2. Double-click it.
3. A terminal window will open and install the required packages.
4. Follow the instructions shown on the screen.
5. When prompted, create the first **Administrator** account.
6. Wait until setup finishes.

This step is normally required only once for each computer.

### Step 5 — Start the website

Whenever you want to use the project:

1. Open the same **E037-ECE-018** folder.
2. Double-click **`run_windows.bat`**.
3. Keep the terminal window open while using the website.

### Step 6 — Open the website

Open your browser and visit:

**http://127.0.0.1:5000**

Sign in using the Administrator username and password that you created during Step 4.

<details>
<summary><b>Having trouble starting the project?</b></summary>

You can also run the files from PowerShell. Open PowerShell inside the main project folder and use:

```powershell
.\setup_windows.bat
```

For normal use after setup:

```powershell
.\run_windows.bat
```

To stop the website, go to the terminal window and press **Ctrl + C**.

</details>

> **Important:** Keep the terminal window open while using the website. The address `127.0.0.1` works on the computer running the application; it is not a public website link.

---

## 🧭 Understanding the Website

The application has two main account types.

| Account | What it can do |
|---|---|
| **Administrator** | Manage users and groups, review requests, run channel allocation, view schedules, check conflicts and access reports. |
| **Group User** | Sign in to the assigned group account, submit channel requests, and view relevant request and schedule information. |

### How to create a Group User account

The first Administrator account is created during setup. To create additional users:

1. Sign in as **Administrator**.
2. Open **User Accounts**.
3. Enter the user's name, username and temporary password.
4. Select the **GROUP_USER** role.
5. Assign the user's active group.
6. Create the account.

The new user can then sign in using the account details provided by the Administrator.

### How the allocation process works

1. A Group User submits a channel and time-slot request.
2. The Administrator reviews the submitted requests.
3. The allocation engine checks the project rules.
4. Valid requests receive channel and time-slot allocations.
5. The resulting schedule and any conflicts can be viewed in the dashboard.

---

## ✨ Main Features

- 🔐 Separate Administrator and Group User accounts.
- 👥 User and group management.
- 📝 Channel and time-slot request submission.
- ⚙️ Automatic channel allocation.
- 📅 Allocation timetable and schedule.
- ⚠️ Conflict detection and logging.
- 📊 Dashboard, utilisation information and reports.
- 📁 CSV output files.
- 🧪 Automated tests for the allocation logic.
- 🖥️ Official Team E037 command-file evaluation.

---

## 📻 Important Allocation Rules

The application follows these main scheduling rules:

| Rule | Explanation |
|---|---|
| **16 channel numbers** | Channels are numbered 1 to 16. |
| **Channel 16** | Always reserved; it is not allocated. |
| **Allocatable channels** | Channels 1 to 15. |
| **Starting frequency** | 446.00625 MHz. |
| **Channel spacing** | 12.5 kHz. |
| **Time-slot duration** | 30 minutes. |
| **Slots per day** | 48. |
| **Maximum continuous duration** | 8 slots (4 hours) per request. |
| **Maximum channels** | 3 channels per group in a time slot. |
| **Priority order** | SECURITY → MEDICAL → EVENTS → MAINTENANCE. |

**Channel conflict rule:** Different groups cannot use the same channel or adjacent channel numbers during the same time slot. The allocation engine checks these conditions before assigning channels.

**All-or-nothing rule:** A request is allocated as a whole or is not allocated. Partial allocation is not allowed.

---

## 🧰 Technical Information

You do not need to understand these technologies to run the application. This section is for readers who want to know how the project was built.

| Part | Technology |
|---|---|
| Programming language | Python |
| Backend | Flask |
| Frontend | HTML, CSS and JavaScript |
| Database | SQLite by default; MySQL is also supported |
| Database ORM | Flask-SQLAlchemy |
| Testing | Pytest |

### Project folder structure

```text
E037-ECE-018/
│
├── app/                # Website pages, routes and application logic
├── docs/               # Design and project documents
├── migrations/         # Database migration files
├── sample_data/        # Sample channels, groups and requests
├── scripts/            # Setup and evaluation scripts
├── tests/              # Automated tests
│
├── config.py           # Application configuration
├── requirements.txt    # Required Python packages
├── run.py              # Application entry point
├── setup_windows.bat   # First-time setup
├── run_windows.bat     # Start the website
└── VERSION.txt         # Project version
```

---

## 🧪 Run the Automated Tests

This step is mainly for developers or evaluators.

1. Complete the setup from the earlier instructions.
2. Open PowerShell inside the main project folder.
3. Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Pytest will run the automated tests and display the results.

## 📄 Run the Official Team E037 Evaluation

The repository includes sample input files and a separate evaluation runner.

1. Open the main project folder.
2. Double-click **`run_official_windows.bat`**.
3. Wait for the evaluation to finish.
4. Open the generated files in:

```text
exports/official_run/
```

The output files are:

- `allocation_table.csv`
- `utilisation.csv`
- `conflict_log.csv`

The sample input files are available in `sample_data/team_e037/`.

---

## 🛠️ Troubleshooting

<details>
<summary><b>Python is not recognised or cannot be found</b></summary>

Install Python 3.10–3.12 from [python.org](https://www.python.org/downloads/). During installation, enable **Add Python to PATH** if available. Close and reopen your terminal after installing.

</details>

<details>
<summary><b>The setup window closes or shows an error</b></summary>

Make sure you are running `setup_windows.bat` from the main project folder. Check your internet connection and read the error shown in the terminal. Do not close the window before noting the error.

</details>

<details>
<summary><b>The website does not open</b></summary>

- Check that `run_windows.bat` is running.
- Keep its terminal window open.
- Make sure you entered **http://127.0.0.1:5000** correctly.
- If another application is using port 5000, the server may fail to start.

</details>

<details>
<summary><b>My login details are not working</b></summary>

Use the Administrator credentials created during the first-time setup. For a Group User account, ask the Administrator to confirm that the account was created and assigned to the correct group.

</details>

<details>
<summary><b>Packages or Python import errors appear</b></summary>

Run `setup_windows.bat` again and allow it to finish. If the issue continues, save the complete terminal error so it can be checked.

</details>

---

## 🔒 Important Notes

- This project is a **software simulation**. It does not transmit radio signals or connect to physical walkie-talkie hardware.
- The application is configured for local use and demonstration.
- Do not share Administrator passwords.
- Do not upload your `.env` file, passwords, local database or private user information to GitHub.
- Do not delete the local database while using the application; it may contain accounts, requests and allocation records.

---

## 📚 Project Documents

The following documents are included in the repository:

| Document | Open |
|---|---|
| System Design Document | [DESIGN_DOCUMENT.pdf](docs/DESIGN_DOCUMENT.pdf) |
| Engineering Decision Log | [DECISION_LOG.md](docs/DECISION_LOG.md) |
| System Architecture | [ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Verification Report | [VERIFICATION_REPORT.md](docs/VERIFICATION_REPORT.md) |
| Automated test suite | [tests/](tests/) |

---

## 👨‍💻 Team Information

| Field | Details |
|---|---|
| **Project title** | Campus Walkie-Talkie Channel and Time-Slot Allocation Engine |
| **Project code** | ECE-018 |
| **Team ID** | E037 |
| **Team members** | Surya Prakash.S, Sudarshan V. |
| **GitHub repository** | [E037-ECE-018](https://github.com/suryaprakashs0629/E037-ECE-018) |

---

<div align="center">

**Team E037 · ECE-018**

*Campus Walkie-Talkie Channel and Time-Slot Allocation Engine*

[⬆ Back to top](#-campus-walkie-talkie-channel--time-slot-allocation-engine)

</div>
