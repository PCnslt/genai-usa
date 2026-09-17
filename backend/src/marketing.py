"""Marketing copy + grounding content for the public website RAG chatbot.

This is the "knowledge base" the sales bot is grounded in (in addition to the
live product catalog). Used both as system-prompt context (Bedrock) and as the
source for the rule-based fallback when Bedrock isn't configured.
"""
from __future__ import annotations

PITCH = (
    "Generative Artificial Intelligence (genai-usa.com) is a productized AI "
    "agency for real estate agents and home-service businesses (plumbers, "
    "electricians, HVAC, landscapers, roofers, cleaners). We build and run the "
    "AI systems that capture leads, answer missed calls, fill the schedule, and "
    "manage reviews — delivered by a vetted expert network on fixed scope and "
    "fixed price, with a human on every plan. Outcomes, not hourly billing."
)

HOW_IT_WORKS = [
    "Pick a service or plan — fixed scope, fixed price, no hourly billing.",
    "We scope it with you and assign a vetted specialist.",
    "We build, QA, and deliver — most systems go live in 48 hours to 2 weeks.",
    "We run and maintain it monthly; a human is always on the line.",
]

VALUE_PROPS = [
    "Fixed price, named outcome — you know exactly what you're buying.",
    "48-hour to 2-week delivery on most systems.",
    "A human on every plan — a 24/7 hotline is included on all retainers.",
    "Built by vetted specialists, QA'd before you ever see it.",
    "Outcome guarantees where it matters (AI SDR: 50 meetings or month 4 free).",
]

GUARANTEES = [
    "Fixed-scope deliverables as described — no hourly surprises.",
    "AI SDR: 50 booked meetings in 90 days, or month 4 is free.",
    "Every retainer includes a 24/7 hotline with a real human.",
]

SERVICES_SUMMARY = (
    "Real estate agents: Missed-Call AI Receptionist, Lead-Qualifier Chatbot, "
    "Lead Follow-Up Automation, CRM Setup (Follow Up Boss/kvCORE), Listing "
    "Marketing Pack, Virtual Staging + Photo Editing, Local SEO + Google "
    "Business, Website + IDX. Home services: Missed-Call AI Receptionist, "
    "Online Booking & Scheduling, Estimate Follow-Up Automation, Google "
    "Business Profile + Reviews, Local SEO + GEO, Website + Online Booking, "
    "Before/After Content, Facebook/Google Ads + Lead Gen."
)

PLANS_SUMMARY = (
    "Retainers (monthly): AI Concierge $4,999 (one system + 24/7 hotline), "
    "AI Growth Team $7,499 (three systems + dedicated account lead), "
    "Fractional AI Department $14,499 (full suite + account manager), "
    "AI Transformation Partner $19,999 (unlimited systems + on-call engineer)."
)

CTA = "Want a quote or a demo? Head to the Plans page or use Contact — we'll scope it and reply fast."


def context() -> str:
    """Compact grounding block for the model's system prompt."""
    return "\n".join([
        PITCH,
        "",
        "How it works:",
        *[f"- {s}" for s in HOW_IT_WORKS],
        "",
        "Why us:",
        *[f"- {s}" for s in VALUE_PROPS],
        "",
        "Services:",
        SERVICES_SUMMARY,
        "",
        "Plans:",
        PLANS_SUMMARY,
    ])
