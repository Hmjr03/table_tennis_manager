# Commercial plans foundation

## Current release rule

The plans page is a product preview. It contains no prices, checkout, payment
provider, card fields or feature enforcement. Existing users retain access to
all current product features. No paid offer may be activated until the legal,
support, tax, refund and operational decisions in the pre-launch checklist are
approved.

## Proposed segmentation

| Plan | Primary audience | Player capacity | Positioning |
| --- | --- | ---: | --- |
| Starter | Individual athlete | 1 | Essential organization and performance record |
| Professional | Athlete or coach | 5 | Continuous development across several profiles |
| Organization | Club or academy | 50 | Structured management for a growing team |

The user role and the commercial plan are independent. An athlete, coach or
club account can be migrated to a different plan without rewriting identity or
sporting data.

## Safety rules before enforcement

1. Limits must not delete or hide existing records.
2. A downgrade must preserve data and restrict only creation beyond capacity.
3. The interface must warn users before a trial or billing period ends.
4. Payment status must be updated only by verified provider webhooks.
5. Every webhook must be idempotent and auditable.
6. Store checkout and web checkout must never create duplicate entitlements.
7. Support must have a documented recovery path for billing errors.

## Decisions required before checkout

- launch countries, currency, taxes and invoice responsibility;
- monthly and annual prices;
- trial duration and whether a card is required;
- cancellation effective date and refund policy;
- grace period for failed payments;
- Apple and Google in-app purchase strategy;
- support contact and response expectations;
- analytics events for acquisition, activation, conversion and churn.

## Recommended implementation sequence

1. Validate the three plan descriptions with pilot users.
2. Approve prices, legal wording and support procedure.
3. Add server-side entitlement checks without enabling them.
4. Integrate a payment provider in sandbox mode.
5. Test purchase, renewal, failed payment, cancellation and restoration.
6. Enable paid plans for an invitation-only pilot.
