# Local acceptance testing

This process creates a demonstration workspace in an isolated database under
`/tmp`. It never uses the normal development or future production database.

## Start the demonstration

Activate the virtual environment from the project directory and run:

```bash
bash scripts/start_acceptance_demo.sh
```

Open `http://127.0.0.1:8001/accounts/login/` and use the credentials printed in
the terminal. Complete the journeys in `PRE_LAUNCH_CHECKLIST.md` in English,
Portuguese and Spanish, including a narrow mobile browser viewport.

Stopping the server does not alter normal local data. The isolated database is
temporary and must never be copied to production.
