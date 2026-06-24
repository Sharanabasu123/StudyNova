# StudyNova

StudyNova is a Flask-based student utility platform built for college students.
This project provides a clean, responsive study portal with user authentication,
note preview/download support, and a modern learning dashboard experience.

## Repository Overview

- `app.py` � Flask application entrypoint and route definitions
- `templates/` � HTML templates for all frontend views
- `static/` � CSS, JavaScript, and asset files
- `requirements.txt` � Python dependencies
- `studynova.db` � local SQLite database used for app data
- `studynova.sql` � SQL schema and seed data references
- `mysql_schema.sql` � MySQL schema and default academic seed script
- `mysql_migration.sql` � MySQL legacy `notes` to `resources` migration script

## Key Features

- Student login, registration, and session management
- Notes upload and preview functionality
- Responsive UI for desktop and mobile layouts
- Flash message support for user feedback
- Basic search and category-based note browsing
- Secure password hashing and validation

## Local Setup

1. Create a Python virtual environment (recommended):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Launch the application:

```powershell
python app.py
```

4. Open your browser:

```text
http://127.0.0.1:5000
```

## Recommended Workflow

- Keep environment-specific files out of the repository
- Use a `.gitignore` file for local caches and secrets
- Update `requirements.txt` when adding new Python packages
- Back up `studynova.db` before making schema changes

## Deployment Notes

This project is prepared for lightweight deployment. For production use,
consider the following:

- Use a production WSGI server (Gunicorn) instead of the Flask dev server
- Move from SQLite to a managed database for better reliability
- Secure secret keys and environment variables outside source control
- Store uploaded files in a dedicated cloud storage service

## GitHub Repository

https://github.com/Sharanabasu123/StudyNova

## License

This project is available under the MIT License unless otherwise specified.
