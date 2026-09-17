"""Marketing copy + grounding content for the public website RAG chatbot.

This is the "knowledge base" the sales bot is grounded in (in addition to the
live product catalog). Used both as system-prompt context (Bedrock) and as the
source for the rule-based fallback when Bedrock isn't configured.

Positioning rule: we NEVER say who we cater to. Services are organized purely
by AI service category. No industry verticals.
"""
from __future__ import annotations

PITCH = (
    "Generative Artificial Intelligence (genai-usa.com) is a productized AI "
    "agency. We build and run the AI systems that answer calls, capture leads, "
    "generate content, and automate operations — organized purely by what the "
    "system does, never by who the customer is. Delivery is fixed scope and "
    "fixed price through a vetted expert network, with a human on every plan. "
    "Outcomes, not hourly billing."
)

HOW_IT_WORKS = [
    "Pick a service, product, or plan — fixed scope, fixed price, no hourly billing.",
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
    "Chat & Phone: Custom AI Chatbot, AI Voice Receptionist, AI Support Agent, "
    "AI That Makes Your Calls. Content & Design: AI Content Engine, AI Social "
    "Media Engine, AI Video & Avatar Production, AI Branding & Creative. "
    "Sales & Leads: AI Lead Generation System, AI Sales Assistant (SDR), AI "
    "Follow-Up & Nurture, AI CRM & Pipeline Automation. Marketing & Ads: "
    "AI SEO Content Pipeline, AI Ads & Creative Optimization, AI Review & "
    "Reputation Management, AI Email Marketing Automation. Operations & Admin: "
    "AI Document Processing, AI Workflow Automation, AI Scheduling & Booking, "
    "AI Internal Knowledge Assistant. Data & Reports: AI Analytics Dashboard, "
    "Predictive AI & Forecasting, AI Market & Competitor Intelligence. "
    "Custom Builds: Custom LLM Application, AI API & System Integration, "
    "Fine-Tuned AI Model, AI Website & Landing Pages."
)

PLANS_SUMMARY = (
    "Retainers (monthly): AI Concierge $4,999 (one system + 24/7 hotline), "
    "AI Growth Team $7,499 (three systems + dedicated account lead), "
    "Fractional AI Department $14,499 (full suite + account manager), "
    "AI Transformation Partner $19,999 (unlimited systems + on-call engineer)."
)

RECOMMEND = (
    "Tell me what you'd like to automate and I'll match you to the right one:\n"
    "- Answering visitor questions & capturing leads → Website AI Chatbot or Custom AI Chatbot.\n"
    "- Questions on your docs & policies → Ask My Docs AI Assistant.\n"
    "- Answering your phone & booking → AI Voice Receptionist.\n"
    "- Finding & qualifying leads → AI Lead Generation System or AI Sales Assistant (SDR).\n"
    "- Content, SEO & ads → AI SEO Content Pack or AI SEO Content Pipeline.\n"
    "Most teams start with a Website AI Chatbot — it answers questions and captures names & emails 24/7. What are you trying to get off your plate?"
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
