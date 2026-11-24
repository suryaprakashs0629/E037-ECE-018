# Database migrations

The project initialisation script uses `db.create_all()` for a straightforward first local setup. Flask-Migrate is also configured for versioned schema changes after the first schema has been created.

From the project root, with `.venv` active and `.env` configured:

```powershell
flask --app run.py db init
flask --app run.py db migrate -m "Initial schema"
flask --app run.py db upgrade
```

For subsequent model changes, run `flask --app run.py db migrate -m "Describe change"` and `flask --app run.py db upgrade`. Review generated migration scripts before applying them. Do not delete or modify the official CSV master files as part of migrations.
