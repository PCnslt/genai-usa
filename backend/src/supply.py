"""Supply & hiring map — who to hire (and at what price) for each thing we sell.

This is the internal "supply chain" reference the founder uses to staff every
service, product, and plan with Fiverr/Upwork contractors. For each line it
lists the roles to fill and the going contractor price, grounded in the pricing
research (Sept 2026 Fiverr/Upwork scrapes). Admin-only — never shown to
customers.

Sell prices are set 3–20× above contractor cost, so every line carries margin.
"""
from __future__ import annotations

# role_key -> {title, gig, fiverr, upwork}
ROLES = {
    "chatbot_dev": {"title": "AI Chatbot Developer", "gig": "AI chatbot development", "fiverr": "med $115 · $20–$2,000", "upwork": "~$25/hr"},
    "rag_engineer": {"title": "RAG / Knowledge-Base Engineer", "gig": "AI integration / RAG", "fiverr": "med $152 · $100–$1,847", "upwork": "~$40/hr"},
    "voice_ai": {"title": "Voice AI Engineer", "gig": "AI voice agent / phone", "fiverr": "med $90 · $10–$490", "upwork": "~$25/hr"},
    "automation": {"title": "Automation Specialist", "gig": "AI workflow (n8n/Make/Zapier)", "fiverr": "med $67 · $10–$600", "upwork": "~$40/hr"},
    "content_writer": {"title": "Content Writer (AI-assisted)", "gig": "AI SEO article writing", "fiverr": "med $10–20/article · $5–$495", "upwork": "~$20/hr"},
    "seo_specialist": {"title": "SEO Specialist", "gig": "SEO audit / optimization", "fiverr": "med $77 · $5–$530", "upwork": "~$25/hr"},
    "brand_designer": {"title": "Brand Designer", "gig": "brand identity design", "fiverr": "med $47 · $20–$325", "upwork": "~$25/hr"},
    "video_producer": {"title": "Video / Avatar Producer", "gig": "AI avatar spokesperson video", "fiverr": "med $15/video · $5–$100", "upwork": "~$25/hr"},
    "social_manager": {"title": "Social Media Manager", "gig": "social media AI", "fiverr": "med $95 · $5–$1,160", "upwork": "~$7/hr"},
    "email_marketer": {"title": "Email Marketing Specialist", "gig": "email marketing automation", "fiverr": "med $30 · $5–$650", "upwork": "~$25/hr"},
    "lead_gen": {"title": "Lead Gen / Outreach Specialist", "gig": "AI lead generation", "fiverr": "med $55 · $5–$1,300", "upwork": "~$8–25/hr"},
    "data_analyst": {"title": "Data Analyst / BI", "gig": "data analysis / dashboard", "fiverr": "med ~$60", "upwork": "~$25–40/hr"},
    "ml_engineer": {"title": "ML Engineer", "gig": "AI/ML development", "fiverr": "—", "upwork": "~$40–144/hr"},
    "fine_tuning": {"title": "LLM Fine-Tuning Engineer", "gig": "LLM fine tuning", "fiverr": "med $100 · $20–$1,800", "upwork": "~$40/hr"},
    "market_researcher": {"title": "Market Researcher", "gig": "market research report", "fiverr": "med $37 · $5–$1,000", "upwork": "—"},
    "web_dev": {"title": "Web Developer", "gig": "website / landing page", "fiverr": "med ~$100", "upwork": "~$25/hr"},
    "ads_specialist": {"title": "Paid Ads Specialist", "gig": "PPC / ads management", "fiverr": "med ~$50", "upwork": "~$25/hr"},
    "doc_extraction": {"title": "Document / Data Extraction", "gig": "data entry / OCR", "fiverr": "med ~$50", "upwork": "~$10/hr"},
    "va": {"title": "VA / Account Manager", "gig": "virtual assistant", "fiverr": "$6–15/hr", "upwork": "~$6–15/hr"},
}

# category -> list of {id, name, kind, sell, roles}
SUPPLY = [
    {"category": "Products (one-time)", "items": [
        {"id": "website-ai-chatbot", "name": "Website AI Chatbot", "kind": "product", "sell": "$2,500", "roles": ["chatbot_dev"]},
        {"id": "ask-my-docs", "name": "Ask My Docs AI Assistant", "kind": "product", "sell": "$3,500", "roles": ["rag_engineer"]},
        {"id": "workflow-automation-setup", "name": "Workflow Automation Setup", "kind": "product", "sell": "$2,500", "roles": ["automation"]},
        {"id": "custom-fine-tuned-model", "name": "Custom Fine-Tuned AI Model", "kind": "product", "sell": "$4,000", "roles": ["fine_tuning"]},
        {"id": "avatar-video-pack", "name": "AI Avatar Video Pack", "kind": "product", "sell": "$1,500", "roles": ["video_producer"]},
        {"id": "seo-content-pack", "name": "AI SEO Content Pack", "kind": "product", "sell": "$2,000", "roles": ["content_writer"]},
        {"id": "seo-audit-roadmap", "name": "AI SEO Audit + Roadmap", "kind": "product", "sell": "$1,000", "roles": ["seo_specialist"]},
        {"id": "brand-identity-kit", "name": "AI Brand Identity Kit", "kind": "product", "sell": "$2,500", "roles": ["brand_designer"]},
    ]},
    {"category": "Chat & Phone", "items": [
        {"id": "ai-chatbot", "name": "Custom AI Chatbot", "kind": "service", "sell": "$1,500 + $300/mo", "roles": ["chatbot_dev", "rag_engineer"]},
        {"id": "ai-voice-receptionist", "name": "AI Voice Receptionist", "kind": "service", "sell": "$1,500 + $300/mo", "roles": ["voice_ai"]},
        {"id": "ai-support-agent", "name": "AI Support Agent", "kind": "service", "sell": "$2,000 + $400/mo", "roles": ["chatbot_dev", "rag_engineer"]},
        {"id": "outbound-ai-calling", "name": "AI That Makes Your Calls", "kind": "service", "sell": "$2,500 + $500/mo", "roles": ["voice_ai"]},
    ]},
    {"category": "Content & Design", "items": [
        {"id": "ai-content-engine", "name": "AI Content Engine", "kind": "service", "sell": "$1,000 + $300/mo", "roles": ["content_writer"]},
        {"id": "ai-social-engine", "name": "AI Social Media Engine", "kind": "service", "sell": "$800 + $250/mo", "roles": ["social_manager"]},
        {"id": "ai-video-avatar", "name": "AI Video & Avatar Production", "kind": "service", "sell": "$1,200/video", "roles": ["video_producer"]},
        {"id": "ai-branding", "name": "AI Branding & Creative", "kind": "service", "sell": "$1,000", "roles": ["brand_designer"]},
    ]},
    {"category": "Sales & Leads", "items": [
        {"id": "ai-lead-gen", "name": "AI Lead Generation System", "kind": "service", "sell": "$2,500 + $500/mo", "roles": ["lead_gen"]},
        {"id": "ai-sdr", "name": "AI Sales Assistant (SDR)", "kind": "service", "sell": "$1,500 + $300/mo", "roles": ["chatbot_dev", "lead_gen"]},
        {"id": "ai-follow-up", "name": "AI Follow-Up & Nurture", "kind": "service", "sell": "$1,200 + $200/mo", "roles": ["email_marketer", "automation"]},
        {"id": "ai-crm", "name": "AI CRM & Pipeline Automation", "kind": "service", "sell": "$1,500", "roles": ["automation"]},
    ]},
    {"category": "Marketing & Ads", "items": [
        {"id": "ai-seo", "name": "AI SEO Content Pipeline", "kind": "service", "sell": "$1,500/mo", "roles": ["seo_specialist", "content_writer"]},
        {"id": "ai-ads", "name": "AI Ads & Creative Optimization", "kind": "service", "sell": "$1,500 + $500/mo", "roles": ["ads_specialist"]},
        {"id": "ai-reputation", "name": "AI Review & Reputation Mgmt", "kind": "service", "sell": "$500 + $300/mo", "roles": ["automation"]},
        {"id": "ai-email-marketing", "name": "AI Email Marketing Automation", "kind": "service", "sell": "$800 + $250/mo", "roles": ["email_marketer"]},
    ]},
    {"category": "Operations & Admin", "items": [
        {"id": "ai-document-processing", "name": "AI Document Processing", "kind": "service", "sell": "$2,000 + $400/mo", "roles": ["doc_extraction", "automation"]},
        {"id": "ai-workflow", "name": "AI Workflow Automation", "kind": "service", "sell": "$1,500 + $300/mo", "roles": ["automation"]},
        {"id": "ai-scheduling", "name": "AI Scheduling & Booking", "kind": "service", "sell": "$800 + $150/mo", "roles": ["automation"]},
        {"id": "ai-knowledge-assistant", "name": "AI Internal Knowledge Assistant", "kind": "service", "sell": "$2,000 + $400/mo", "roles": ["rag_engineer"]},
    ]},
    {"category": "Data & Reports", "items": [
        {"id": "ai-analytics", "name": "AI Analytics Dashboard", "kind": "service", "sell": "$2,500 + $500/mo", "roles": ["data_analyst"]},
        {"id": "ai-forecasting", "name": "Predictive AI & Forecasting", "kind": "service", "sell": "$3,000 + $750/mo", "roles": ["ml_engineer", "data_analyst"]},
        {"id": "ai-competitive-intel", "name": "AI Market & Competitor Intel", "kind": "service", "sell": "$1,500/mo", "roles": ["market_researcher"]},
    ]},
    {"category": "Custom Builds", "items": [
        {"id": "custom-llm-app", "name": "Custom LLM Application", "kind": "service", "sell": "$5,000", "roles": ["ml_engineer"]},
        {"id": "ai-api-integration", "name": "AI API & System Integration", "kind": "service", "sell": "$3,000", "roles": ["ml_engineer"]},
        {"id": "fine-tuned-model", "name": "Fine-Tuned AI Model", "kind": "service", "sell": "$5,000 + $500/mo", "roles": ["fine_tuning"]},
        {"id": "ai-website", "name": "AI Website & Landing Pages", "kind": "service", "sell": "$3,500", "roles": ["web_dev", "chatbot_dev"]},
    ]},
    {"category": "Plans (retainer)", "items": [
        {"id": "plan-concierge", "name": "AI Concierge", "kind": "plan", "sell": "$4,999/mo", "roles": ["va", "chatbot_dev"]},
        {"id": "plan-growth", "name": "AI Growth Team", "kind": "plan", "sell": "$7,499/mo", "roles": ["va", "chatbot_dev", "content_writer"]},
        {"id": "plan-fractional", "name": "Fractional AI Department", "kind": "plan", "sell": "$14,499/mo", "roles": ["va", "chatbot_dev", "automation", "content_writer", "seo_specialist"]},
        {"id": "plan-transformation", "name": "AI Transformation Partner", "kind": "plan", "sell": "$19,999/mo", "roles": ["va", "ml_engineer", "automation", "content_writer"]},
    ]},
]
