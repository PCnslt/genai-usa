"""Product catalog — single source of truth for what we sell.

Seeded into the `genai-products` DynamoDB table by `backend/seed.py`. The
`GET /products` endpoint reads from DynamoDB (admin-editable); this module is
the initial seed AND the fallback when the table is empty.

Positioning rule: we NEVER say who we cater to. Services are organized purely
by AI service category (`category` field). No industry verticals.

Two kinds of buyable things:
  - `product` — ONE-TIME purchase, "buy once, own forever" (build-and-handover
    or a one-time deliverable). No monthly subscription.
  - `service` — managed/done-for-you work (we build AND run it; many carry a
    monthly component).
  - `plan` — monthly retainer.
"""
from __future__ import annotations

CATALOG = [
    # ---- one-time products (buy once, own forever — no subscription) ----
    dict(product_id="website-ai-chatbot", name="Website AI Chatbot", kind="product",
         category="Chat & Phone",
         price_cents=250000, monthly_cents=0, recurring=False,
         description="An AI assistant added to your website that answers visitor questions and captures names and emails — built and handed over so you own it and host it on your own site. No subscription; it keeps working forever."),
    dict(product_id="ask-my-docs", name="Ask My Docs AI Assistant", kind="product",
         category="Operations & Admin",
         price_cents=350000, monthly_cents=0, recurring=False,
         description="A private AI assistant trained on your documents, manuals, and policies that answers questions in plain language with citations — deployed in your own environment. Yours to keep, no ongoing fee."),
    dict(product_id="workflow-automation-setup", name="Workflow Automation Setup", kind="product",
         category="Operations & Admin",
         price_cents=250000, monthly_cents=0, recurring=False,
         description="Automations that connect your existing tools so repetitive jobs run themselves — built inside your own n8n, Make, or Zapier account, so you own and control them forever."),
    dict(product_id="custom-fine-tuned-model", name="Custom Fine-Tuned AI Model", kind="product",
         category="Custom Builds",
         price_cents=400000, monthly_cents=0, recurring=False,
         description="A model trained on your data, voice, and tasks — delivered with the trained files and a run guide. You own the model outright and run it yourself, no subscription."),
    dict(product_id="avatar-video-pack", name="AI Avatar Video Pack", kind="product",
         category="Content & Design",
         price_cents=150000, monthly_cents=0, recurring=False,
         description="A set of finished, ready-to-post videos featuring an AI spokesperson — explainers, ads, or onboarding. Delivered as video files you own and reuse forever, no re-licensing fee."),
    dict(product_id="seo-content-pack", name="AI SEO Content Pack", kind="product",
         category="Marketing & Ads",
         price_cents=200000, monthly_cents=0, recurring=False,
         description="Ten publish-ready, keyword-optimized articles written and edited for you — delivered as files you own and publish on your own site. You keep every article forever."),
    dict(product_id="seo-audit-roadmap", name="AI SEO Audit + Roadmap", kind="product",
         category="Marketing & Ads",
         price_cents=100000, monthly_cents=0, recurring=False,
         description="A one-time deep review of your site's search performance plus a prioritized fix-it roadmap — a report you keep and can implement yourself or hand to anyone."),
    dict(product_id="brand-identity-kit", name="AI Brand Identity Kit", kind="product",
         category="Content & Design",
         price_cents=250000, monthly_cents=0, recurring=False,
         description="A complete visual identity — logo, color palette, typography, and a style guide — delivered as files you own outright. One-time, no license or subscription."),

    # ---- Chat & Phone ----
    dict(product_id="ai-chatbot", name="Custom AI Chatbot", kind="service",
         category="Chat & Phone",
         price_cents=150000, monthly_cents=30000, recurring=True,
         description="A website and in-app assistant trained on your products, documents, and FAQs. It answers like your best rep — grounded, on-brand, 24/7 — and hands off to a human the moment a conversation needs one."),
    dict(product_id="ai-voice-receptionist", name="AI Voice Receptionist", kind="service",
         category="Chat & Phone",
         price_cents=150000, monthly_cents=30000, recurring=True,
         description="An AI phone agent that answers on the first ring, books appointments, takes messages, and routes urgent calls — in a natural, human voice, around the clock."),
    dict(product_id="ai-support-agent", name="AI Support Agent", kind="service",
         category="Chat & Phone",
         price_cents=200000, monthly_cents=40000, recurring=True,
         description="Resolves repeat customer questions across chat and email by reading your knowledge base — escalating only the cases that genuinely need a human."),
    dict(product_id="outbound-ai-calling", name="AI That Makes Your Calls", kind="service",
         category="Chat & Phone",
         price_cents=250000, monthly_cents=50000, recurring=True,
         description="An AI agent that makes confirmation, reminder, and follow-up calls at scale, updates your records automatically, and never needs a break."),

    # ---- Content & Design ----
    dict(product_id="ai-content-engine", name="AI Content Engine", kind="service",
         category="Content & Design",
         price_cents=100000, monthly_cents=30000, recurring=True,
         description="Long-form articles, newsletters, and email copy researched, drafted, and edited in your voice — delivered on a schedule, publication-ready."),
    dict(product_id="ai-social-engine", name="AI Social Media Engine", kind="service",
         category="Content & Design",
         price_cents=80000, monthly_cents=25000, recurring=True,
         description="A full month of scroll-stopping posts, captions, and short-form video scripts — planned, written, and scheduled across every platform you care about."),
    dict(product_id="ai-video-avatar", name="AI Video & Avatar Production", kind="service",
         category="Content & Design",
         price_cents=120000, monthly_cents=0, recurring=False,
         description="Faceless videos, AI presenters, and UGC-style ads produced end-to-end from a single brief — no studio, no shoot, no editing backlog. Priced per video."),
    dict(product_id="ai-branding", name="AI Branding & Creative", kind="service",
         category="Content & Design",
         price_cents=100000, monthly_cents=0, recurring=False,
         description="A complete visual identity — logo, palette, type, and ad creative — generated and refined into a polished brand kit your team can use everywhere."),

    # ---- Sales & Leads ----
    dict(product_id="ai-lead-gen", name="AI Lead Generation System", kind="service",
         category="Sales & Leads",
         price_cents=250000, monthly_cents=50000, recurring=True,
         description="An outbound engine that finds, enriches, and qualifies prospects — then hands you a steady stream of warm, ready-to-book conversations."),
    dict(product_id="ai-sdr", name="AI Sales Assistant (SDR)", kind="service",
         category="Sales & Leads",
         price_cents=150000, monthly_cents=30000, recurring=True,
         description="Qualifies inbound leads in seconds, answers objections in your voice, and books meetings straight into your calendar — day and night."),
    dict(product_id="ai-follow-up", name="AI Follow-Up & Nurture", kind="service",
         category="Sales & Leads",
         price_cents=120000, monthly_cents=20000, recurring=True,
         description="Multi-channel sequences across email, SMS, and voice that work every lead for 90 days — and never let one go cold."),
    dict(product_id="ai-crm", name="AI CRM & Pipeline Automation", kind="service",
         category="Sales & Leads",
         price_cents=150000, monthly_cents=0, recurring=False,
         description="Your CRM configured with lead scoring and smart automations so every contact is worked, prioritized, and never dropped."),

    # ---- Marketing & Ads ----
    dict(product_id="ai-seo", name="AI SEO Content Pipeline", kind="service",
         category="Marketing & Ads",
         price_cents=150000, monthly_cents=150000, recurring=True,
         description="Search-optimized content and technical SEO that compounds — climbing you up the rankings month over month with content people actually search for."),
    dict(product_id="ai-ads", name="AI Ads & Creative Optimization", kind="service",
         category="Marketing & Ads",
         price_cents=150000, monthly_cents=50000, recurring=True,
         description="Paid campaigns with AI-generated creative and copy, continuously tested and optimized against the metrics that matter."),
    dict(product_id="ai-reputation", name="AI Review & Reputation Management", kind="service",
         category="Marketing & Ads",
         price_cents=50000, monthly_cents=30000, recurring=True,
         description="Collect, monitor, and respond to reviews across every platform automatically — your rating improves on autopilot."),
    dict(product_id="ai-email-marketing", name="AI Email Marketing Automation", kind="service",
         category="Marketing & Ads",
         price_cents=80000, monthly_cents=25000, recurring=True,
         description="Segmented campaigns and lifecycle flows that turn a static list into predictable revenue — welcome, win-back, and promotions that send themselves."),

    # ---- Operations & Admin ----
    dict(product_id="ai-document-processing", name="AI Document Processing", kind="service",
         category="Operations & Admin",
         price_cents=200000, monthly_cents=40000, recurring=True,
         description="Extract, classify, and file data from invoices, contracts, and forms automatically — no more manual data entry."),
    dict(product_id="ai-workflow", name="AI Workflow Automation", kind="service",
         category="Operations & Admin",
         price_cents=150000, monthly_cents=30000, recurring=True,
         description="Your tools connected with AI steps that handle the busywork — routing, triaging, and updating systems without a human in the loop."),
    dict(product_id="ai-scheduling", name="AI Scheduling & Booking", kind="service",
         category="Operations & Admin",
         price_cents=80000, monthly_cents=15000, recurring=True,
         description="Self-serve booking, calendar sync, and reminder messages that run themselves while you work."),
    dict(product_id="ai-knowledge-assistant", name="AI Internal Knowledge Assistant", kind="service",
         category="Operations & Admin",
         price_cents=200000, monthly_cents=40000, recurring=True,
         description="A private assistant grounded in your policies, SOPs, and documents — instant, cited answers for your whole team."),

    # ---- Data & Reports ----
    dict(product_id="ai-analytics", name="AI Analytics Dashboard", kind="service",
         category="Data & Reports",
         price_cents=250000, monthly_cents=50000, recurring=True,
         description="A live dashboard that turns your data into plain-English insights, trends, and anomalies — no analyst required."),
    dict(product_id="ai-forecasting", name="Predictive AI & Forecasting", kind="service",
         category="Data & Reports",
         price_cents=300000, monthly_cents=75000, recurring=True,
         description="Models that forecast demand, churn, and revenue so you decide ahead of the market instead of reacting to it."),
    dict(product_id="ai-competitive-intel", name="AI Market & Competitor Intelligence", kind="service",
         category="Data & Reports",
         price_cents=150000, monthly_cents=150000, recurring=True,
         description="Automated monitoring of competitors, pricing, and brand mentions — briefed to you weekly with what to do about it."),

    # ---- Custom Builds ----
    dict(product_id="custom-llm-app", name="Custom LLM Application", kind="service",
         category="Custom Builds",
         price_cents=500000, monthly_cents=0, recurring=False,
         description="A bespoke AI tool built around your exact workflow — from a written spec to production, with your data and your rules."),
    dict(product_id="ai-api-integration", name="AI API & System Integration", kind="service",
         category="Custom Builds",
         price_cents=300000, monthly_cents=0, recurring=False,
         description="AI wired into your existing stack — CRM, ERP, website, or internal tools — so it works where your team already lives."),
    dict(product_id="fine-tuned-model", name="Fine-Tuned AI Model", kind="service",
         category="Custom Builds",
         price_cents=500000, monthly_cents=50000, recurring=True,
         description="A model trained on your data, tone, and domain for the job only you do — consistently on-brand, at scale."),
    dict(product_id="ai-website", name="AI Website & Landing Pages", kind="service",
         category="Custom Builds",
         price_cents=350000, monthly_cents=0, recurring=False,
         description="A conversion-focused site with an embedded AI assistant, live in two weeks — designed to capture, qualify, and convert."),

    # ---- monthly retainer plans ----
    dict(product_id="plan-concierge", name="AI Concierge", kind="plan",
         category="Retainers",
         price_cents=499900, recurring=True, monthly_cents=499900,
         description="One AI system working around the clock — with a 24/7 hotline, so you're never left stuck."),
    dict(product_id="plan-growth", name="AI Growth Team", kind="plan",
         category="Retainers",
         price_cents=749900, recurring=True, monthly_cents=749900,
         description="Three systems running your growth — plus a dedicated person who knows your business."),
    dict(product_id="plan-fractional", name="Fractional AI Department", kind="plan",
         category="Retainers",
         price_cents=1449900, recurring=True, monthly_cents=1449900,
         description="A complete AI team — strategy, systems, and management — without hiring a single person."),
    dict(product_id="plan-transformation", name="AI Transformation Partner", kind="plan",
         category="Retainers",
         price_cents=1999900, recurring=True, monthly_cents=1999900,
         description="We run AI across your whole organization — unlimited systems and an on-call engineer."),
]


def by_id() -> dict:
    return {p["product_id"]: p for p in CATALOG}


def by_kind(kind: str) -> list:
    return [p for p in CATALOG if p["kind"] == kind]
