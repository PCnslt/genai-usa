"""Clickwrap contract terms (ToS + Service Agreement).

Single source of truth for the active contract version. The Lambda stores the
acceptance (version, IP, UA, timestamp) in `genai-contracts`; checkout is gated
on an accepted active version. An admin can override the text/version at
runtime via `POST /ops/contracts/template` (stored in `genai-meta`).

NOTE: this text is a solid starting point but is NOT a substitute for review by
a licensed attorney — especially the limitation-of-liability and refund
clauses, which are the parts that keep the business "off the hook".
"""
from __future__ import annotations

VERSION = "1.0"

TERMS_TEXT = """TERMS OF SERVICE & SERVICE AGREEMENT
Version 1.0 — Last updated September 17, 2026

1. PARTIES
This agreement is between you ("Client", "you") and Generative Artificial
Intelligence ("Company", "we", "us"), operating at genai-usa.com.

2. SERVICES
We provide AI systems, automation, content, and related professional services
(the "Services"). Services are delivered by our vetted expert network. By
purchasing, you agree to these terms.

3. PAYMENT
(a) One-time fees are due at purchase. (b) Retainer and subscription fees are
billed monthly in advance and are non-refundable once the billing cycle begins.
(c) You authorize us to charge the payment method on file.

4. NO-GUARANTEE / NO-REFUND POLICY
(a) Custom work is non-refundable once work begins. (b) We do not guarantee
specific business results (revenue, leads, or conversions). (c) Fixed-scope
deliverables are delivered as described; revisions are limited to the scope
stated at purchase. (d) The only exception to no-refunds is an outcome
guarantee where one is explicitly offered (for example, the AI SDR program's
"50 booked meetings in 90 days, or month 4 is free").

5. INTELLECTUAL PROPERTY
Upon full payment, we assign you ownership of the specific deliverables
produced for you. We retain ownership of our underlying tools, templates, and
know-how, which may be licensed to other clients.

6. CONFIDENTIALITY
Each party agrees to protect the other's confidential information and not
disclose it except as necessary to perform the Services.

7. NO WARRANTIES
The Services are provided "as is" and "as available", without warranties of any
kind, express or implied, including merchantability, fitness for a particular
purpose, or non-infringement.

8. LIMITATION OF LIABILITY
To the maximum extent permitted by law, the Company's total liability for any
claim arising from the Services is limited to the amount you paid for the
specific service in the three (3) months preceding the claim. The Company is
not liable for indirect, incidental, special, consequential, or punitive
damages, or for lost profits, data, or revenue.

9. INDEMNIFICATION
You agree to indemnify and hold the Company harmless against claims arising
from your use of the Services or your content.

10. TERMINATION
Either party may terminate a retainer with thirty (30) days written notice.
Upon termination you owe fees accrued through the effective date.

11. GOVERNING LAW
This agreement is governed by the laws of the United States, in the venue
designated by the Company, without regard to conflict-of-law principles.

12. ENTIRE AGREEMENT
These terms, together with any statement of work, constitute the entire
agreement and supersede prior agreements.

By checking the box and completing your purchase, you acknowledge that you have
read, understood, and agree to be bound by these terms.
"""
