# Pre-launch approval checklist

Use this checklist before inviting external users or accepting payment. Every
required item must have an owner, evidence and an approval date. A successful
deployment alone is not a release approval.

## 1. Product and user journeys

- [ ] Registration, email verification, sign-in and password recovery work.
- [ ] A user can create, edit and delete their own players, matches,
      competitions, calendar events, transactions and notes.
- [ ] Dashboard dates, next commitments and statistics use the expected time
      zone and only the signed-in user's data.
- [ ] Empty states, validation errors and destructive confirmations are clear.
- [ ] Portuguese, Spanish and English journeys have no untranslated controls.

## 2. Privacy and account control

- [ ] Terms and Privacy Policy show the correct controller, contact and version.
- [ ] Registration records acceptance of the current legal documents.
- [ ] Data export produces a complete, readable file for the signed-in user.
- [ ] Account deletion requires confirmation and removes the expected data.
- [ ] Test accounts and test personal data are removed after acceptance testing.

## 3. Security and operations

- [ ] GitHub checks pass on the exact commit selected for release.
- [ ] Render build, migration and readiness checks pass with `DJANGO_DEBUG=False`.
- [ ] No password, token, database URL or secret appears in Git or screenshots.
- [ ] HTTPS works and secure cookies are confirmed in the browser.
- [ ] Database backup and isolated restore verification are documented.
- [ ] Error logs and health checks are reviewed without exposing personal data.

## 4. Email and domain

Follow `operations/EMAIL_AND_DOMAIN.md` and attach the provider and DNS
verification evidence to the release record.

- [ ] The production sender domain and SMTP provider are configured.
- [ ] Verification and password-reset emails arrive in major email providers.
- [ ] SPF, DKIM and DMARC records pass the provider's verification.
- [ ] The temporary Render address passes acceptance before the custom domain.
- [ ] The custom domain receives a valid HTTPS certificate before public launch.

## 5. Mobile and commercial readiness

Follow `operations/COMMERCIAL_PLANS.md` before enabling any entitlement limit
or payment provider.

- [ ] Essential pages work on a small Android screen and on an iPhone/iPad.
- [ ] PWA installation, icons, offline screen and updates work as expected.
- [ ] Pricing, billing cycle, cancellation and refund rules are approved before
      any paid offer is displayed.
- [ ] Support contact and incident responsibility are assigned.
- [ ] A small invitation-only pilot is approved before broad marketing.

## Release decision

- Release commit:
- Environment and URL:
- Reviewer:
- Approval date:
- Known limitations accepted:
- Decision: **GO / NO-GO**
