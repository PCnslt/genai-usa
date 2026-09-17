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

    # ---- services (setup + optional monthly) — real estate + home services ----
    dict(product_id="missed-call-receptionist", name="Missed-Call AI Receptionist", kind="service",
         price_cents=150000, monthly_cents=30000, recurring=False,
         description="An AI voice receptionist that answers 24/7, books the job or showing, and texts confirmation. Live in 48 hours."),
    dict(product_id="lead-qualifier-chatbot", name="Lead-Qualifier Chatbot", kind="service",
         price_cents=150000, monthly_cents=30000, recurring=False,
         description="Qualifies Zillow/website/Facebook leads in seconds and books the call into your CRM. Live in 2 weeks."),
    dict(product_id="lead-follow-up-automation", name="Lead Follow-Up Automation", kind="service",
         price_cents=120000, recurring=False,
         description="A text + email drip that works every lead for 90 days, with missed-call text-back."),
    dict(product_id="crm-setup", name="CRM Setup (Follow Up Boss / kvCORE)", kind="service",
         price_cents=100000, recurring=False,
         description="Pipeline, smart plans, and automations configured so every lead is worked."),
    dict(product_id="listing-marketing-pack", name="Listing Marketing Pack", kind="service",
         price_cents=50000, recurring=False,
         description="MLS-ready descriptions, a property flyer, and two weeks of social posts for one listing."),
    dict(product_id="virtual-staging", name="Virtual Staging + Photo Editing", kind="service",
         price_cents=3500, recurring=False,
         description="Photorealistic furniture staging and flambient color editing. Priced per photo."),
    dict(product_id="local-seo-google", name="Local SEO + Google Business", kind="service",
         price_cents=150000, recurring=True, monthly_cents=150000,
         description="Rank in Google Maps with citations and a reviews system."),
    dict(product_id="real-estate-website", name="Real Estate Website + IDX", kind="service",
         price_cents=350000, recurring=False,
         description="A lead-generating site with live MLS/IDX search and an embedded chatbot."),
    dict(product_id="online-booking", name="Online Booking & Scheduling", kind="service",
         price_cents=80000, recurring=False,
         description="Self-serve booking with calendar sync and reminder texts."),
    dict(product_id="estimate-follow-up", name="Estimate Follow-Up Automation", kind="service",
         price_cents=120000, recurring=False,
         description="Automated quote reminders and win-back sequences that turn estimates into booked jobs."),
    dict(product_id="gbp-reviews", name="Google Business Profile + Reviews", kind="service",
         price_cents=50000, monthly_cents=30000, recurring=False,
         description="An optimized profile plus a review-request system that fills your star rating."),
    dict(product_id="local-seo-geo", name="Local SEO + GEO", kind="service",
         price_cents=150000, recurring=True, monthly_cents=150000,
         description="Rank in Google Maps and in ChatGPT/Perplexity when homeowners ask for the best local provider."),
    dict(product_id="website-booking", name="Website + Online Booking", kind="service",
         price_cents=250000, recurring=False,
         description="A fast, mobile-first site with booking, built for your trade."),
    dict(product_id="before-after-content", name="Before/After Content", kind="service",
         price_cents=2500, recurring=False,
         description="Realistic after-renderings and edited before/afters. Priced per image."),
    dict(product_id="ads-lead-gen", name="Facebook / Google Ads + Lead Gen", kind="service",
         price_cents=150000, recurring=False,
         description="Lead campaigns that keep your calendar full — for plumbers, HVAC, roofers, and landscapers."),

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
