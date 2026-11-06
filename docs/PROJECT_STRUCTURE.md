# Project structure

- `app/services/allocation_engine.py`: pure allocation rules, independent of Flask.
- `app/services/command_runner.py`: official E037 commands.txt processor and exact CSV writer.
- `app/models.py`: SQLAlchemy persistence models.
- `app/routes.py`: authenticated website routes and user workflows.
- `app/templates/`: multi-page Jinja UI.
- `app/static/css/app.css`: navy/blue/light neutral design system.
- `app/static/js/app.js`: sidebar, dismissible messages and confirmation interactions.
- `sample_data/team_e037/`: the actual Team E037 channels.csv, groups.csv, commands.txt and official README.
- `scripts/init_db.py`: create local tables and load official masters.
- `scripts/create_admin.py`: interactively create initial admin credentials.
- `scripts/run_official.py`: standalone evaluation runner, no Flask/MySQL required.
- `tests/`: automated tests for official input and allocation rules.
