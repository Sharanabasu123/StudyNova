# StudyNova Admin Credentials

StudyNova no longer stores production admin passwords in source code.

## Production Setup

Set these environment variables before the first production startup:

```bash
STUDYNOVA_SECRET_KEY=<strong-random-secret>
STUDYNOVA_ADMIN_EMAIL=<admin-email>
STUDYNOVA_ADMIN_PASSWORD=<strong-admin-password>
STUDYNOVA_ADMIN_NAME=StudyNova Admin
```

If no admin user exists and the admin environment variables are missing, the app will not create a default admin account.

## Local Existing Database

Existing local database users are preserved by migrations. Changing these environment variables does not delete or modify existing users.

## Optional Development Demo User

Demo user seeding is disabled by default. To seed a local-only demo user on an empty database, set:

```bash
STUDYNOVA_CREATE_DEMO_USER=1
```

Do not enable demo users in production.
