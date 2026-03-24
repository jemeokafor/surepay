# Sure-Pay BRD

- **Project:** Sure-Pay
- **Version:** 2.1 Operator-Safe MVP
- **Date:** March 14, 2026
- **Market:** Nigeria social commerce on Instagram, X, and WhatsApp
- **Category:** Buyer-protected checkout and delayed vendor payout infrastructure

## 1. Product Thesis

Nigerian social commerce loses conversion because buyers do not trust prepayment and vendors do not trust "send account number, I'll pay later."

Sure-Pay solves this with a lightweight storefront and payment-link layer that lets buyers pay through a trusted gateway while delaying vendor payout until delivery is confirmed or uncontested.

Sure-Pay is not a marketplace. It is checkout, trust, and payout infrastructure for off-platform sellers.

Sure-Pay must also make trust cumulative and visible. Each completed protected transaction should increase a vendor's public settlement history so future buyers rely less on unverified delivery claims and more on prior released outcomes.

For MVP, Sure-Pay should be described as **buyer-protected checkout** or **delayed payout protection**, not **trustless escrow**, until legal review confirms that claim.

## 2. Product Goals

- Increase DM-to-payment conversion for vendors.
- Give buyers confidence to pay online for informal social-commerce transactions.
- Allow Sure-Pay to safely hold, release, refund, and audit transactions.
- Keep onboarding fast enough for solo sellers while enforcing enough controls to move real money safely.
- Turn completed protected transactions into visible trust mass that compounds future conversion.

## 3. Non-Goals

- No multi-item carts.
- No in-app messaging or negotiation.
- No logistics integration.
- No crypto, BNPL, subscriptions, or international payments.
- No partial refunds in V1.
- No public marketplace discovery feed.

## 4. Core Users

### Vendor

Social seller of fashion, beauty, gadgets, or services; wants a trusted payment flow without building a store.

### Buyer

Skeptical consumer; wants assurance that payment does not equal immediate vendor access to funds.

### Admin/Ops

Sure-Pay operator; reviews disputes, monitors payouts, handles exceptions, and protects the system from fraud and payout errors.

## 5. Product Principles

- Buyer trust is the conversion engine.
- Funds do not become payable to the vendor until a valid release event occurs.
- Payment success is confirmed only by Paystack webhook, never by frontend redirect alone.
- Every transaction state change must create an audit event.
- Guest buyers are allowed; vendors must authenticate.
- Manual admin arbitration is acceptable in MVP; ambiguous automation is not.
- Where delivery cannot be machine-verified, public trust should be derived from immutable settlement history rather than vendor self-claims.

## 6. Success Metrics

- Vendor completes signup and creates first live checkout in under 5 minutes.
- Paid transactions move to `FUNDS_LOCKED` only after successful webhook verification.
- Duplicate webhook delivery never creates duplicate payouts.
- Median dispute resolution time is under 48 hours.
- Payout success rate stays above 95%.
- Dispute rate, refund rate, and payout failure rate are visible on an admin dashboard from day one.
- Storefronts with visible trust metrics outperform storefronts without them on checkout conversion.

## 7. Product Scope

- **Vendor side:** auth, onboarding, bank setup, custom payment links, 3-item storefront, transaction ledger, delivery marking, dispute evidence upload, public trust badge sharing.
- **Buyer side:** secure checkout, receipt/status page, signed re-access link, confirm delivery, report issue, visible vendor settlement history.
- **Admin side:** dispute queue, evidence viewer, refund/release actions, payout monitor, vendor restriction controls.
- **System side:** webhooks, scheduled jobs, notifications, audit logs, idempotency, payout retries, trust metric aggregation.

## 8. End-to-End Transaction Flow

1. Vendor signs up, creates a username, completes payout details, and verifies a transfer recipient.
2. Vendor generates either a custom one-off payment link or a public storefront with up to 3 featured items.
3. Buyer opens checkout, sees item snapshot and trust messaging, and pays through Paystack.
4. Paystack webhook verifies payment and moves the transaction to `FUNDS_LOCKED`.
5. Vendor fulfills the order off-platform.
6. Vendor marks the item as delivered.
7. Transaction moves to `AWAITING_BUYER_CONFIRMATION` and a 24-hour buyer action window starts.
8. Buyer either confirms delivery or opens a dispute.
9. If the buyer does nothing for 24 hours after delivery is marked, the transaction auto-releases.
10. Once released, Sure-Pay creates a payout record and transfers the vendor's net amount.
11. When payout succeeds, Sure-Pay updates the vendor's public settlement metrics and badge.
12. If instead a dispute is resolved for the buyer, Sure-Pay issues a refund instead of payout.

## 9. State Machine

```text
PENDING_PAYMENT
  -> FUNDS_LOCKED
  -> EXPIRED
  -> CANCELLED

FUNDS_LOCKED
  -> AWAITING_BUYER_CONFIRMATION
  -> DISPUTED
  -> REFUNDED
  -> CANCELLED

AWAITING_BUYER_CONFIRMATION
  -> RELEASED
  -> DISPUTED
  -> REFUNDED

DISPUTED
  -> RELEASED
  -> REFUNDED

Terminal states:
RELEASED, REFUNDED, EXPIRED, CANCELLED
```

## 10. State Definitions

- **PENDING_PAYMENT:** checkout exists but payment has not been confirmed; expires after 24 hours.
- **FUNDS_LOCKED:** payment is confirmed and funds are reserved for this transaction; vendor has not yet been paid.
- **AWAITING_BUYER_CONFIRMATION:** vendor has marked the order delivered; buyer now has 24 hours to confirm or dispute.
- **DISPUTED:** buyer or admin has halted release pending manual review.
- **RELEASED:** buyer has confirmed delivery or the post-delivery window expired without dispute; vendor is entitled to payout.
- **REFUNDED:** buyer receives funds back; vendor is not paid.
- **EXPIRED:** unpaid checkout expired.
- **CANCELLED:** admin/system closed the transaction before payout or refund completion.

## 11. Critical Operating Rules

- The 24-hour auto-release timer starts only after `AWAITING_BUYER_CONFIRMATION`, never at payment time.
- Vendor cannot receive payout directly at `FUNDS_LOCKED`.
- Buyer can dispute non-delivery while a transaction is still `FUNDS_LOCKED` if the vendor has not fulfilled within the fulfillment SLA.
- Default fulfillment SLA for MVP is `7 days` from `paid_at`; after that, buyer may open a non-delivery dispute.
- Payment verification must be webhook-driven and idempotent.
- Transaction state and payout state are separate; `RELEASED` does not guarantee transfer success.
- Refund and payout actions must be admin- or system-triggered through the backend only.
- Every dispute, release, refund, payout failure, and manual override must be logged.
- Public trust metrics must be system-derived from immutable events and payouts; vendors cannot edit or inflate them manually.
- Positive trust counters must only use transactions that reach `RELEASED` and `payouts.status = succeeded`; `REFUNDED`, `EXPIRED`, and `CANCELLED` transactions are excluded from positive trust totals, while dispute outcomes remain separately visible.

## 12. Functional Requirements

### 12.1 Authentication and Onboarding

- Support Google OAuth and email magic-link login via Supabase Auth.
- Vendor can reserve a unique `username` used for `surepay.link/@username`.
- Vendor may sign up quickly, but cannot publish storefront or generate live payment links until payout details are verified.
- Required payout setup before activation: `bank_code`, `account_number`, `account_name`, and Paystack `recipient_code`.
- Vendor onboarding target is under 2 minutes excluding bank verification delays.

### 12.2 Vendor Dashboard

- Show `gross volume`, `funds locked`, `released transactions`, `disputed transactions`, and `payout status`.
- Allow vendor to generate a custom link with `item name`, `price_ngn`, and buyer contact details.
- Allow vendor to manage exactly `3 featured items` for the public storefront.
- Show a ledger of all transactions with filters by status, date, and amount.
- Provide actions for `mark delivered`, `view buyer status`, and `submit dispute evidence`.
- Provide payout settings and transfer-recipient verification status.
- Provide a preview and copy/export action for the vendor's live public trust badge.

### 12.3 Public Storefront

- Public route: `surepay.link/@username`.
- Show vendor brand name, avatar, short bio, trust message, and 3 featured items.
- Show a prominent `Settlement Gravity Panel` with live trust metrics derived from completed protected transactions.
- Each item includes a secure CTA that creates a transaction snapshot and opens checkout.
- Storefront must be fast, mobile-first, and readable without login.
- The public trust panel should include, at minimum, `protected sales count`, `released volume`, `successful payouts`, `last completed settlement`, and `resolved disputes`.
- If the vendor is new and has insufficient history, the panel should clearly show `New on Sure-Pay` rather than implying invisible trust.

### 12.4 Secure Checkout

- Route pattern: `/pay/{transaction_id}` or `/checkout/{transaction_id}`.
- Show item snapshot, vendor identity, amount, and clear buyer-protection explanation.
- Collect `buyer_name`, `buyer_email`, and `buyer_whatsapp`.
- Use Paystack to initialize payment.
- Do not mark payment as successful until backend webhook confirms it.
- Buyer total equals listed item price; Sure-Pay fee is deducted from vendor payout in MVP.

### 12.5 Buyer Receipt and Status Page

- Show payment receipt, order timeline, vendor name, and current transaction status.
- Generate a signed buyer re-access link immediately after payment.
- Send the buyer a magic-link receipt by email for recovery and follow-up.
- Allow buyer to `Confirm Delivery` or `Report Issue` when eligible.
- Show countdown when the transaction is in `AWAITING_BUYER_CONFIRMATION`.
- Show a trust snapshot of the vendor's completed protected history to reinforce cumulative confidence during post-payment follow-up.

### 12.6 Disputes and Arbitration

- Buyer can open a dispute for `non-delivery`, `wrong item`, `damaged item`, `counterfeit`, or `materially not as described`.
- Vendor can upload proof such as delivery evidence, chat proof, or item condition evidence.
- Admin can request more evidence, resolve in favor of vendor, or resolve in favor of buyer.
- V1 dispute outcomes are only `RELEASED` or `REFUNDED`; no partial split decisions.

### 12.7 Admin Console

- Show all transactions by status and risk level.
- Show dispute queue, payout queue, failed transfers, and overdue fulfillments.
- Allow manual release, refund, cancellation, and vendor suspension with reason logging.
- Show full event timeline and evidence files per transaction.

### 12.8 Notifications

- Required for MVP: email notifications for payment received, delivery marked, dispute opened, dispute resolved, and payout completed.
- Optional stretch: SMS or WhatsApp alerts if a provider is already available.
- Notification delivery attempts and failures should be logged.

### 12.9 Settlement Gravity System

- Sure-Pay must compute a public trust profile for each active vendor using immutable `transactions`, `payouts`, `disputes`, and `transaction_events` data.
- The public trust profile must be shown on the storefront, on checkout, and on buyer receipt/status pages.
- The system must generate a signed, shareable public badge/card that vendors can post on Instagram highlights, WhatsApp catalogs, and X profiles.
- Badge data must refresh automatically after qualifying release, payout success, refund resolution, or dispute resolution events.
- Public metrics must never be vendor-editable and must be rendered from backend-controlled endpoints or server-side pages only.
- Minimum public metrics for MVP: `protected sales`, `released NGN volume`, `successful payouts`, `last payout time`, and `resolved disputes`.
- The badge should link back to the vendor storefront or trust page so off-platform viewers can verify that the metrics are live.
- Positive trust totals must be computed from transactions whose payout has fully succeeded, not from delivery marks or pending releases.

## 13. Payment, Refund, and Payout Policy

- **Payment initiation:** frontend requests backend to create a Paystack transaction reference.
- **Payment confirmation:** backend verifies via webhook signature and reference lookup.
- **Refunds:** only admin/system initiated in V1; frontend never calls Paystack refunds directly.
- **Payouts:** triggered only after transaction becomes `RELEASED`.
- **Transfer failure:** payout record becomes `FAILED`, ops is alerted, and retry logic starts; transaction remains `RELEASED`.
- **Fee model:** Sure-Pay takes `1.5%` from vendor proceeds; validate that this covers Paystack fees, transfer fees, and dispute operations before launch.
- **MVP risk cap:** impose a per-transaction cap, recommended default `NGN 250,000`, adjustable by admin.

## 14. Trust and Growth Loops

- Replace `Verified Escrow` language with `Buyer Protected by Sure-Pay`.
- Replace the static trust badge concept with a live `Settlement Gravity Badge` generated from actual protected transaction history.
- Every successful protected transaction should increase the vendor's public trust mass and make future buyers more likely to convert.
- On buyer success/receipt pages, show a seller-acquisition CTA: "Do you sell online? Start accepting protected payments with Sure-Pay."
- Use Paystack trust cues where policy allows, but explain Sure-Pay protection in plain language rather than invented jargon.
- The trust loop should reduce delivery-proof friction by letting new buyers evaluate cumulative settlement history, not just the current vendor promise.

## 15. Recommended Technical Architecture

- **Frontend:** `Next.js` web app for storefront, checkout, vendor dashboard, and admin dashboard.
- **Backend:** `FastAPI` for business rules, webhooks, dispute actions, and payout orchestration.
- **Database/Auth/Storage:** `Supabase` for PostgreSQL, Auth, row-level security, and evidence/image storage.
- **Payments:** `Paystack` transactions, transfer recipients, transfers, refunds, and webhooks.
- **Background jobs:** cron/worker for expiry, auto-release, payout retries, and overdue fulfillment checks.
- **Email:** `Resend` or `Postmark`.
- **Observability:** structured logs plus error monitoring such as `Sentry`.
- **Trust aggregation:** server-side metrics pipeline or materialized view for vendor public trust profiles and signed badge rendering.

## 16. Architecture Notes

- `Streamlit` is not recommended for the public buyer experience or mobile-first storefronts.
- If a Python-only prototype is unavoidable, use Streamlit only for internal admin or ops tooling, not the customer-facing checkout.
- Buyers should never query Supabase directly for transaction control; buyer actions should go through signed backend endpoints.
- Vendor-facing tables should use Supabase RLS; admin actions should run through backend service-role endpoints only.
- Public trust metrics should be derived from append-only events and settlement records, then cached for read performance.
- Public badge endpoints should be signed and cacheable so vendors can embed them off-platform without exposing write surfaces.

## 17. Data Model

### `vendors`

- `id uuid pk` linked to `auth.users.id`
- `username text unique not null`
- `display_name text not null`
- `email text not null`
- `phone text`
- `brand_bio text`
- `avatar_url text`
- `bank_code text`
- `account_number text`
- `account_name text`
- `recipient_code text`
- `payout_ready boolean default false`
- `trust_badge_enabled boolean default true`
- `status enum(active, restricted, suspended)`
- `created_at`, `updated_at`

### `products`

- `id uuid pk`
- `vendor_id uuid fk`
- `name text not null`
- `description text`
- `image_url text`
- `price_ngn integer not null`
- `is_featured boolean default false`
- `is_active boolean default true`
- `sort_order integer`
- `created_at`, `updated_at`
- Business rule: maximum `3` featured items per vendor, enforced in backend and DB trigger

### `transactions`

- `id uuid pk`
- `vendor_id uuid fk`
- `product_id uuid fk nullable`
- `source enum(custom_link, storefront)`
- `product_name text not null`
- `product_snapshot jsonb not null`
- `buyer_name text`
- `buyer_email text not null`
- `buyer_whatsapp text`
- `amount_ngn integer not null`
- `fee_ngn integer not null`
- `vendor_net_ngn integer not null`
- `currency text default NGN`
- `status enum(PENDING_PAYMENT, FUNDS_LOCKED, AWAITING_BUYER_CONFIRMATION, DISPUTED, RELEASED, REFUNDED, EXPIRED, CANCELLED)`
- `payment_status enum(INITIATED, PENDING, SUCCESS, FAILED, REFUNDED)`
- `paystack_reference text unique`
- `paystack_access_code text`
- `buyer_access_token_hash text`
- `expires_at`
- `paid_at`
- `delivery_marked_at`
- `auto_release_at`
- `released_at`
- `refunded_at`
- `cancelled_at`
- `created_at`, `updated_at`

### `disputes`

- `id uuid pk`
- `transaction_id uuid unique fk`
- `opened_by enum(buyer, admin, system)`
- `reason_code enum(non_delivery, wrong_item, damaged_item, counterfeit, not_as_described, other)`
- `description text`
- `buyer_evidence jsonb`
- `vendor_evidence jsonb`
- `status enum(open, under_review, resolved_release, resolved_refund, cancelled)`
- `resolution_notes text`
- `resolved_by uuid nullable`
- `opened_at`, `resolved_at`, `updated_at`

### `payouts`

- `id uuid pk`
- `transaction_id uuid unique fk`
- `vendor_id uuid fk`
- `amount_ngn integer not null`
- `recipient_code text not null`
- `transfer_reference text unique`
- `status enum(queued, processing, succeeded, failed, reversed)`
- `failure_reason text`
- `attempt_count integer default 0`
- `initiated_at`, `succeeded_at`, `failed_at`, `updated_at`

### `transaction_events`

- `id bigserial pk`
- `transaction_id uuid fk`
- `actor_type enum(buyer, vendor, admin, system, webhook)`
- `actor_id uuid nullable`
- `event_type text not null`
- `payload jsonb`
- `created_at`

### `notification_logs` (recommended)

- `id uuid pk`
- `transaction_id uuid nullable`
- `recipient_type enum(buyer, vendor, admin)`
- `channel enum(email, sms, whatsapp)`
- `template_key text`
- `status enum(queued, sent, failed)`
- `error_message text`
- `created_at`, `sent_at`

### `vendor_public_metrics`

- `vendor_id uuid pk fk`
- `protected_sales_count integer default 0`
- `released_volume_ngn bigint default 0`
- `successful_payouts_count integer default 0`
- `resolved_disputes_count integer default 0`
- `buyer_favor_resolutions_count integer default 0`
- `vendor_favor_resolutions_count integer default 0`
- `last_completed_settlement_at timestamptz`
- `last_successful_payout_at timestamptz`
- `trust_score_version text`
- `updated_at timestamptz`
- This table or materialized view must be derived from immutable settlement records, never vendor input.

## 18. Security and Control Requirements

- Verify Paystack webhook signatures.
- Enforce idempotency on webhook processing and payout creation.
- Store no card details.
- Hash buyer access tokens before storage.
- Restrict vendor data using Supabase RLS.
- Require backend-only admin operations.
- Keep immutable event logs for all sensitive actions.
- Rate-limit checkout initialization and dispute creation endpoints.
- Restrict evidence file uploads by size and content type.
- Ensure public trust metrics cannot be spoofed by unsigned client-side requests or editable profile fields.

## 19. Acceptance Criteria

- Vendor can sign up, reserve username, verify payout account, and publish a storefront.
- Vendor can create a one-off payment link in under 60 seconds.
- Buyer can pay via Paystack and see a valid receipt/status page.
- Successful payment updates transaction state only after webhook confirmation.
- Vendor cannot receive payout before `RELEASED`.
- Buyer can re-open the order from a signed email link without creating an account.
- Vendor can mark delivery and trigger a 24-hour buyer action window.
- Buyer can confirm delivery or open a dispute with evidence.
- Admin can resolve disputes to either `RELEASED` or `REFUNDED`.
- Replayed webhooks do not create duplicate transactions, events, or payouts.
- Failed payouts are visible to ops and retried safely.
- Storefront works well on mobile and desktop.
- Storefront, checkout, and buyer receipt pages display live vendor trust metrics sourced from backend settlement data.
- Vendors can copy a signed public trust badge link for use on off-platform social surfaces.

## 20. Out of Scope for V1

- Multi-item cart.
- Buyer accounts with full profile/history.
- Logistics API integrations.
- Partial refunds and split decisions.
- In-app chat.
- Advanced KYC document collection.
- Public reviews, ratings, and recommendation feeds.

## 21. Recommended Build Order

1. Finalize enums, schema, indexes, RLS, and event model.
2. Build vendor auth, username reservation, and payout-recipient setup.
3. Build storefront and custom-link creation flows.
4. Build checkout initialization and Paystack webhook handling.
5. Build buyer receipt/status page with signed re-access links.
6. Build delivery marking, auto-release job, and dispute creation flow.
7. Build settlement metric aggregation and the signed public trust badge.
8. Build admin dispute console and payout monitor.
9. Add notifications, retries, observability, and risk caps.

## 22. Default Decisions Locked In

- Public product claim: `buyer-protected checkout`, not `trustless escrow`.
- Public UX stack: `Next.js`, not Streamlit.
- Buyer recovery method: signed email magic link after payment.
- Auto-release starts after `delivery_marked_at`, not `paid_at`.
- Fulfillment SLA before non-delivery dispute: `7 days`.
- V1 dispute outcomes: `release` or `refund` only.
- V1 automated notifications: email first, WhatsApp later if available.
- Live settlement trust metrics are mandatory on public storefronts and buyer-facing status pages.
- Public trust metrics are system-derived and shareable, never vendor-authored.
