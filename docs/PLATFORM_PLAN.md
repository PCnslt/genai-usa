# Generative Artificial Intelligence — Customer Platform

A customer portal for the products + services sold on genai-usa.com:
login (role-separated), purchase/billing, contracts, a RAG support bot, and
dashboards for customers / employees / admins. Everything on AWS free tier.

## Architecture

| Layer | Service | Notes |
|---|---|---|
| Portal frontend | S3 + CloudFront (`/app/`) | static SPA, no build step |
| Auth + roles | Cognito User Pool + groups `customers` / `employees` / `admins` | hosted UI login |
| Backend | API Gateway (HTTP API) + Lambda (Python) | JWT authorizer (Cognito) |
| Data | DynamoDB | users, products, orders, entitlements, contracts, billing, chat |
| Payments | **Abstract provider layer** → Stripe (now) / PayPal / bank (later) | idempotent + swappable |
| Contracts | Clickwrap (now) → DocuSign API (later) | stored, timestamped |
| RAG chatbot | Bedrock Knowledge Bases + DynamoDB customer-data grounding | Claude + Titan |

**Fixed cost ≈ $0–5/mo** (Cognito/Lambda/DynamoDB/S3 all free tier; Bedrock is
usage-priced, ~$1–5/mo at low volume; Stripe is ~2.9% + $0.30 per sale only).

## Data model (DynamoDB)

- `genai-products` — catalog. PK `product_id`.
- `genai-orders` — PK `order_id`, GSI `customer_id`. Holds `idempotency_key`.
- `genai-entitlements` — PK `customer_id`, SK `product_id` (what a customer owns).
- `genai-contracts` — PK `contract_id`, GSI `customer_id` (clickwrap acceptances).
- `genai-billing` — PK `payment_id`, GSI `customer_id` (charges + invoices).
- `genai-chat` — PK `session_id`, SK `ts` (optional chat history).

## Phases

### Phase 1 — Foundation (auth, roles, data, portal shell)
- Cognito user pool + 3 groups + hosted UI.
- DynamoDB tables above.
- Portal: login redirect + dashboard shell with left "my purchases" panel.
- Backend: `auth.py` (JWT→role/customer_id), `entitlements` + `orders` list endpoints.

### Phase 2 — Payments (swappable, idempotent)
- `payments.py` abstract provider (create_checkout / parse_event / verify /
  get_billing / refund) + registry + `get_provider()` factory.
- `MockProvider` (works now, no keys) + `StripeProvider` (enabled by env).
- `POST /orders` (create order → checkout) and `POST /webhooks/payments`
  (idempotent event → grant entitlement + write billing).
- Stripe Customer Portal URL for self-serve billing info (later, real provider).

### Phase 3 — Contracts (clickwrap → e-sign)
- `POST /contracts/accept` — store acceptance (version, ip, ts, device).
- Checkout gated on an active accepted contract.
- DocuSign/Dropbox-Sign adapter slots into the same `contracts` module later.

### Phase 4 — RAG support bot
- `POST /chat` — grounds the answer in (a) the customer's own entitlements +
  orders from DynamoDB and (b) service/product docs via Bedrock KB; answers
  with Claude. Falls back to a rule-based answer if Bedrock is not configured.

### Phase 5 — Employee + admin dashboards
- Employees: view orders, move fulfillment status, see contracts, respond to
  customer messages (the ops/orchestrator view).
- Admins: manage products/pricing, users/roles, contract templates, finance.

## Payment abstraction (the switchable part)

`backend/src/payments.py`:
- `PaymentProvider` ABC — the only interface the rest of the code touches.
- `register(name)` + `get_provider()` — provider chosen by `PROVIDER_NAME` env.
- Every `Order` has an `idempotency_key`; every webhook `Event` has an
  `event_id`. Handlers dedupe on these so retries/re-deliveries are safe.
- Adding a new provider (PayPal, ACH/bank, etc.) = one new module + registry
  entry; zero changes to handlers or the portal.
