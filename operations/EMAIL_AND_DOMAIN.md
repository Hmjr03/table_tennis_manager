# Transactional email and sender-domain runbook

Use this runbook before inviting external users. The recommended configuration
on Render is Resend through its HTTPS API. SMTP remains supported on hosts that
permit outbound SMTP connections. Provider credentials and DNS records must
never be committed to Git.

## 1. Sender identity

1. Choose a dedicated transactional subdomain, such as
   `mail.tabletennismanager.com`.
2. Use a recognizable sender, for example
   `Table Tennis Manager <noreply@tabletennismanager.com>`.
3. Keep a monitored support address visible on the legal and support pages.
4. Separate transactional email from future marketing campaigns.

## 2. Application configuration

### Recommended: Resend API on Render

Configure these environment variables in the production hosting dashboard:

```text
DJANGO_EMAIL_BACKEND=anymail.backends.resend.EmailBackend
RESEND_API_KEY=<secret created in the Resend dashboard>
DJANGO_DEFAULT_FROM_EMAIL=Table Tennis Manager <noreply@verified-domain.example>
DJANGO_PASSWORD_RESET_TIMEOUT=3600
```

The Resend key must be stored only as a secret environment variable. Do not
paste it into source code, documentation, screenshots, tickets or chat.

### Alternative: SMTP on a compatible host

```text
DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
DJANGO_DEFAULT_FROM_EMAIL=Table Tennis Manager <noreply@tabletennismanager.com>
DJANGO_EMAIL_HOST=<provider SMTP hostname>
DJANGO_EMAIL_PORT=587
DJANGO_EMAIL_HOST_USER=<provider SMTP username>
DJANGO_EMAIL_HOST_PASSWORD=<provider SMTP password or API credential>
DJANGO_EMAIL_USE_TLS=True
DJANGO_EMAIL_TIMEOUT=10
DJANGO_PASSWORD_RESET_TIMEOUT=3600
```

Never place real credentials in `.env.example`, GitHub, screenshots, tickets
or chat messages. Rotate a credential immediately if it is exposed.

## 3. DNS authentication

Copy the exact records supplied by the selected email provider:

- SPF: authorize the provider without creating multiple SPF TXT records.
- DKIM: publish every provider-supplied selector and wait for verification.
- DMARC: begin with reporting, inspect results, and strengthen enforcement only
  after SPF and DKIM alignment are consistently healthy.
- Return-Path or bounce domain: configure it when the provider supports it.

DNS names and values are provider-specific. Do not invent, shorten or reuse
records from another service.

## 4. Acceptance test

Use a non-production test account and verify all three messages:

1. new-account verification;
2. password recovery;
3. external account-deletion confirmation.

For each message, record:

- delivery time and inbox/spam placement;
- sender name and From address;
- subject, text version and HTML version;
- button and fallback URL behavior;
- language (English, Portuguese and Spanish);
- one-hour expiration and single-use behavior;
- SPF, DKIM and DMARC result headers.

Test at least Gmail, Outlook and one additional mailbox used by the pilot
audience. Do not launch while verification or recovery mail is unreliable.

## 5. Operations and privacy

- Enable bounce and complaint monitoring with the provider.
- Do not log message bodies, secure tokens or SMTP credentials.
- Set alerts for unusual sending volume and repeated delivery failures.
- Document the provider account owner and credential-rotation responsibility.
- Review suppression lists before investigating a user-reported missing email.
- Keep transactional retention and provider data-processing terms aligned with
  the published Privacy Policy.

## Approval evidence

- Provider:
- Sender domain:
- From address:
- SPF verified:
- DKIM verified:
- DMARC verified:
- Gmail test:
- Outlook test:
- Additional mailbox test:
- Reviewer:
- Approval date:
- Decision: **GO / NO-GO**
