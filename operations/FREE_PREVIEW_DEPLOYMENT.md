# Free validation preview on Render

This preview is for private product validation only. It must not accept
payments or be advertised as the production service.

## Resources and limitations

The `render.preview.yaml` Blueprint creates resources that are independent from
the paid production configuration:

- a free web service named `table-tennis-manager-preview`;
- a free PostgreSQL database named `table-tennis-manager-preview-db`;
- console-only email delivery, so no real verification or password-reset email
  is sent during this preview.

Render can suspend the web service after inactivity and its free PostgreSQL
database expires after 30 days. Never enter irreplaceable personal data in this
environment.

## Deploy

1. Create a new Blueprint from `Hmjr03/table_tennis_manager`.
2. Select branch `main`.
3. Set **Blueprint Path** to `render.preview.yaml`.
4. Confirm that every proposed resource name ends in `-preview` and every plan
   is `free`.
5. Deploy and wait for both resources to become available.

Do not associate the preview Blueprint with the existing production database.

## Validate

Use the temporary `onrender.com` address and verify the health endpoints,
authentication screens, core CRUD journeys, translations and mobile layout.
Because email is console-only, activation links are visible only in private
service logs. Replace this backend with a real transactional email provider
before inviting external users.
