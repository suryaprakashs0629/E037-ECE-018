# Database schema management

The application initialises a fresh local schema through `python scripts/init_db.py`, which calls SQLAlchemy `create_all()` and loads the official channel/group master records. Flask-Migrate is registered in the app factory for versioned schema changes as development continues.

To start tracking schema revisions after dependencies are installed:

```powershell
flask --app run.py db init
flask --app run.py db migrate -m "Initial schema"
flask --app run.py db upgrade
```

For a clean first run, use `scripts/init_db.py`; do not run `db init` more than once in an existing migrations directory. Keep generated migration revisions in source control.
