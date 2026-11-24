# Project structure

## Application

- `app/__init__.py`: Flask application factory; creates runtime upload/export folders.
- `app/routes.py`: authenticated web routes, role checks and user workflows.
- `app/models.py`: SQLAlchemy persistence models and constraints.
- `app/extensions.py`: shared Flask extensions.
- `app/services/allocation_engine.py`: framework-independent allocation rules.
- `app/services/command_runner.py`: official command parser, allocator integration and CSV writer.
- `app/templates/`: Jinja pages for administrator and group-user workflows.
- `app/static/`: application CSS and JavaScript.

## Supporting files

- `config.py`: environment-driven Flask and database configuration.
- `run.py`: local Flask entry point.
- `scripts/init_db.py`: initialise database and load official masters.
- `scripts/create_admin.py`: create the first administrator account.
- `scripts/run_official.py`: run the official command-file evaluation without starting Flask.
- `scripts/seed_masters.py`: seed channel and group master data.
- `sample_data/team_e037/`: supplied official channels, groups, commands and reference README.
- `tests/`: automated tests for official input, allocation rules, CSV output and deterministic behaviour.
- `migrations/`: database migration instructions and future revision storage.
- `docs/`: architecture, design, decisions, verification and source specifications.

## Runtime-only paths

The application creates `instance/`, `uploads/` and `exports/` as required. Logs may be created by the runtime environment. These generated/local paths are excluded from version control and are not required in the source ZIP.
