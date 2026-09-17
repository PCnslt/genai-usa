"""Product catalog — single source of truth for what we sell.

Seeded into the `genai-products` DynamoDB table by `backend/seed.py`. The
`GET /products` endpoint reads from DynamoDB (admin-editable); this module is
the initial seed AND the fallback when the table is empty.
"""
from __future__ import annotations

CATALOG = [
    # ---- one-time products ----
    dict(product_id="prompt-packs", name="Prompt Packs", kind="product",
         price_cents=1499, recurring=False,
         description="Tested prompt libraries for marketing, sales, and operations — plug in and go."),
    dict(product_id="gpt-configs", name="Custom GPT Configs", kind="product",
         price_cents=1900, recurring=False,
         description="Ready-made AI assistants for ChatGPT and Claude — your AI role in a box."),
    dict(product_id="workflow-templates", name="AI Workflow Templates", kind="product",
         price_cents=1900, recurring=False,
         description="Pre-built automations for Zapier, Make, and n8n — import and customize."),
    dict(product_id="notion-kits", name="Notion Template Kits", kind="product",
         price_cents=1900, recurring=False,
         description="Complete workspaces with databases, views, and AI-integrated workflows."),
    dict(product_id="playbooks", name="AI Industry Playbooks", kind="product",
         price_cents=2900, recurring=False,
         description="Implementation guides for your vertical — prompts, workflows, and case studies."),
    dict(product_id="ebooks", name="AI E-books & Lead Magnets", kind="product",
         price_cents=900, recurring=False,
         description="Done-for-you guides and lead magnets — AI-drafted, human-edited."),
    dict(product_id="asset-bundles", name="AI Asset Bundles", kind="product",
         price_cents=1900, recurring=False,
         description="Logos, icons, and social templates — licensed for commercial use."),
    dict(product_id="niche-tool", name="Niche AI Tool", kind="product",
         price_cents=900, recurring=True, monthly_cents=900,
         description="A purpose-built AI micro-app for your specific workflow."),
    dict(product_id="community", name="AI Community", kind="product",
         price_cents=900, recurring=True, monthly_cents=900,
         description="Prompts, templates, and office hours in a gated space for your niche."),

    # ---- services (setup + optional monthly) ----
    dict(product_id="missed-call-recovery", name="Missed-Call Recovery", kind="service",
         price_cents=150000, monthly_cents=75000, recurring=False,
         description="A live AI voice receptionist that answers on the first ring, books the calendar, and sends SMS confirmation in 60 seconds. Live in 48 hours."),
    dict(product_id="support-chatbot", name="Support & FAQ Chatbot", kind="service",
         price_cents=150000, monthly_cents=30000, recurring=False,
         description="A customer-service bot trained on your docs and helpdesk, answering 24/7 without hallucinated fluff. Live in 7–10 days."),
    dict(product_id="lead-qualifier", name="Inbound Lead-Qualifier", kind="service",
         price_cents=500000, monthly_cents=250000, recurring=False,
         description="Chat + SMS + voice agent that captures intent, qualifies budget and fit, books the call, and drops a brief in your CRM. Live in 2 weeks."),
    dict(product_id="workflow-automation", name="Workflow Automation", kind="service",
         price_cents=150000, monthly_cents=30000, recurring=False,
         description="A manual workflow removed end to end — lead routing, data entry, reporting, CRM sync — via Zapier, Make, or n8n."),
    dict(product_id="ai-sdr", name="AI SDR (Outbound)", kind="service",
         price_cents=750000, recurring=False,
         description="A managed outbound program with a named outcome: 50 booked meetings in 90 days, or month 4 is on us."),
    dict(product_id="data-insights", name="Data & Insights", kind="service",
         price_cents=150000, monthly_cents=30000, recurring=False,
         description="Automated dashboards, document processing, and meeting summaries that turn raw data into decisions."),
    dict(product_id="content-engine", name="AI Content Engine", kind="service",
         price_cents=100000, recurring=True, monthly_cents=100000,
         description="12 social posts + 4 emails + 2 blog articles every month — drafted by AI, polished by humans, on-brand and on schedule."),
    dict(product_id="video-ugc", name="AI Video & UGC Bundles", kind="service",
         price_cents=200000, recurring=False,
         description="10–30 ad-ready short-form clips with captions and voiceover for TikTok, Instagram, and Meta."),
    dict(product_id="branding-visuals", name="AI Branding & Visuals", kind="service",
         price_cents=18900, recurring=False,
         description="Logos, product shots, and ad creatives, generated and refined to spec — ready to use."),
    dict(product_id="voice-audio", name="AI Voice & Audio", kind="service",
         price_cents=10000, recurring=False,
         description="Voiceovers, narration, and podcast production in any language and tone."),
    dict(product_id="localization", name="AI Localization", kind="service",
         price_cents=50000, recurring=False,
         description="Translate and localize sites, docs, and subtitles — AI-first with human proofreading."),
    dict(product_id="website-rebuild", name="AI-Native Website Rebuild", kind="service",
         price_cents=450000, recurring=False,
         description="A 2-week rebuild with new copy and an embedded chat + voice + booking agent. Replaces a $15K agency build."),
    dict(product_id="roadmap-audit", name="AI Roadmap & Audit", kind="service",
         price_cents=300000, recurring=False,
         description="A ranked map of where AI saves you time and money, with a phased build plan and dollar impact."),
    dict(product_id="geo-audit", name="AI Visibility (GEO) Audit", kind="service",
         price_cents=50000, recurring=False,
         description="A 7-point audit of where you're cited — and not — across ChatGPT, Claude, Perplexity, and Gemini, with a fix roadmap."),
    dict(product_id="team-training", name="Team Training", kind="service",
         price_cents=200000, recurring=False,
         description="A 4-week bootcamp that gets your team productive with Claude, ChatGPT, and agent thinking."),
    dict(product_id="ai-integration", name="AI Integration", kind="service",
         price_cents=250000, recurring=False,
         description="Embed generative AI into your CRM, ERP, CMS, or helpdesk — without rebuilding anything."),

    # ---- monthly retainer plans ----
    dict(product_id="plan-concierge", name="AI Concierge", kind="plan",
         price_cents=499900, recurring=True, monthly_cents=499900,
         description="One AI system working around the clock — with a 24/7 hotline, so you're never left stuck."),
    dict(product_id="plan-growth", name="AI Growth Team", kind="plan",
         price_cents=749900, recurring=True, monthly_cents=749900,
         description="Three systems running your growth — plus a dedicated person who knows your business."),
    dict(product_id="plan-fractional", name="Fractional AI Department", kind="plan",
         price_cents=1449900, recurring=True, monthly_cents=1449900,
         description="A complete AI team — strategy, systems, and management — without hiring a single person."),
    dict(product_id="plan-transformation", name="AI Transformation Partner", kind="plan",
         price_cents=1999900, recurring=True, monthly_cents=1999900,
         description="We run AI across your whole organization — unlimited systems and an on-call engineer."),
]


def by_id() -> dict:
    return {p["product_id"]: p for p in CATALOG}


def by_kind(kind: str) -> list:
    return [p for p in CATALOG if p["kind"] == kind]
