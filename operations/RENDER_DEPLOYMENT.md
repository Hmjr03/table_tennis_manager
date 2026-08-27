# Private production deployment on Render

Complete `operations/PRE_LAUNCH_CHECKLIST.md` before inviting external users or
accepting payment.

This runbook publishes Table Tennis Manager without placing passwords or API
keys in Git. The Blueprint creates a paid web service and a paid PostgreSQL
database in Frankfurt. Review Render's displayed monthly price before applying
the Blueprint.

## Before deployment

1. Push the tested release to the repository's default branch.
2. Choose an SMTP provider and have these values ready:
   - sender, for example `Table Tennis Manager <noreply@your-domain>`;
   - SMTP host;
   - SMTP username;
   - SMTP password or API credential.
3. Keep the first URL private while completing acceptance tests.

Never place SMTP credentials, database URLs, secret keys or Render API keys in
the repository, screenshots or support messages.

## Create the private environment

1. In Render, open **Blueprints** and choose **New Blueprint Instance**.
2. Connect the `Hmjr03/table_tennis_manager` repository.
3. Select the repository's default branch and the `render.yaml` Blueprint.
4. Review the paid `starter` web service and `basic-256mb` database.
5. Enter the SMTP values requested by Render. It generates the Django secret
   automatically and connects PostgreSQL through its private network.
6. Apply the Blueprint and wait for the health check to become healthy.

The release runs static-file preparation and Django production checks during
the build. Database migrations run separately before the new release goes
live. If a required step fails, the release must not replace the last healthy
version.

## First acceptance test

Use the temporary `onrender.com` address and verify:

1. `/health/live/` returns `{"status": "ok"}`.
2. `/health/ready/` returns `{"status": "ok"}`.
3. Create a new test account and receive the verification email.

Configure the sender and DNS using `operations/EMAIL_AND_DOMAIN.md` before
inviting external users.
4. Log in, add a test athlete, match, calendar event, transaction and note.
5. Change the language between Portuguese, Spanish and English.
6. Install the PWA on one Android device and add it to the home screen on one
   iPhone or iPad.
7. Export the test account's data, then delete the test account.
8. Review Render logs for unexpected errors without copying private data.

Do not invite paying customers until this checklist passes.

## Custom domain (later)

After acquiring and controlling `tabletennismanager.com`, add
`app.tabletennismanager.com` to the Render web service and create the DNS entry
shown by Render. Then set:

- `DJANGO_ALLOWED_HOSTS=app.tabletennismanager.com`
- `DJANGO_CSRF_TRUSTED_ORIGINS=https://app.tabletennismanager.com`

Wait for HTTPS verification before sharing the address. Increase HSTS gradually
only after the final domain and every required subdomain work correctly.
