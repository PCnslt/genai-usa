"""Internal company knowledge base — grounds the staff assistant.

This is the "we dogfood our own product" layer: the same RAG assistant we sell
to customers (AI Internal Knowledge Assistant) is what our own staff uses to
answer questions about how genai-usa operates. Kept separate from marketing.py
(which is public-facing and shipped to the sales bot).
"""
from __future__ import annotations

INTERNAL_DOCS = [
    ("Pricing & margin",
     "Our catalog prices are set 3-10x above Fiverr/Upwork delivery cost. "
     "Retainers: AI Concierge $4,999/mo, AI Growth Team $7,499/mo, Fractional "
     "AI Department $14,499/mo, AI Transformation Partner $19,999/mo. Never "
     "discount below published pricing without founder approval."),
    ("Delivery process",
     "Most systems go live in 48 hours to 2 weeks. Work is delivered through a "
     "vetted expert network (Fiverr/Upwork contractors), QA'd internally before "
     "the customer ever sees it. Advance fulfillment in the Ops console from "
     "pending to in_progress to delivered."),
    ("Contractor relay",
     "Contractors never learn the customer's real identity — they see "
     "Client #XXXX. Customers never learn they're talking to a contractor — "
     "they see an Account Manager. Never reveal either side's identity in any "
     "message or channel."),
    ("Support process",
     "Customers message us inside their portal (Support tab). Reply in the Ops "
     "console Support inbox. Resolve threads when done. Every retainer includes "
     "a 24/7 hotline with a real human on the line."),
    ("Stack",
     "We run on AWS: Cognito (auth), Lambda + API Gateway (backend), DynamoDB "
     "(data), S3 + CloudFront (site + portal). The payment layer is swappable "
     "(mock now, Stripe ready). CloudFormation is the source of truth, in the "
     "genai-usa repo."),
    ("Contacts",
     "Customer email: hello@genai-usa.com. Escalate blockers to the founder."),
]


def context() -> str:
    return "\n\n".join(f"{topic}:\n{text}" for topic, text in INTERNAL_DOCS)
