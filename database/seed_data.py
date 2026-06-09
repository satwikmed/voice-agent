"""
VoiceIQ Seed Data Generator
============================

Pre-populates voiceiq.db with:
- 6 test scenarios
- 18 realistic, varied conversation transcripts with pre-computed judge evaluations
- 18 calibration entries with illustrative human scores

This seed data ensures the Streamlit Cloud demo is fully populated on first load
without requiring Ollama. Every tab renders meaningfully out of the box.

NOTE: The human scores in judge_calibration are ILLUSTRATIVE PLACEHOLDERS.
Replace them with your own hand-scores using `python calibration/harness.py`
for authentic calibration results.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Any

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()
DATABASE_PATH = os.getenv("DATABASE_PATH", "voiceiq.db")

# ── Default agent system prompt used in seeded runs ──────────────────────────

DEFAULT_AGENT_PROMPT = """You are a professional AI sales representative for TechFlow, a B2B SaaS platform that provides workflow automation, CRM, and analytics tools.

CORE RULES:
- Be helpful, professional, and empathetic at all times.
- Answer questions directly — don't dodge or over-qualify.
- Pricing: Starter $29/seat/mo, Professional $79/seat/mo, Enterprise $149/seat/mo (volume discounts available for 50+ seats).
- Deployment: Cloud-hosted, typical onboarding 2-3 weeks, enterprise deployments 4-6 weeks.
- Key differentiators: real-time analytics dashboard, native Salesforce/HubSpot integration, SOC 2 Type II compliance, 99.9% uptime SLA.
- Refund policy: 30-day money-back guarantee, escalate complex cases to a manager.
- Never trash-talk competitors. Focus on your strengths.
- Keep responses concise but complete. No filler phrases.
"""

# ── Scenario definitions ─────────────────────────────────────────────────────

SCENARIO_ROWS = [
    {
        "scenario_name": "Interested Buyer",
        "scenario_description": "A warm, cooperative prospect actively looking for a SaaS solution. They want to understand core features, pricing tiers, and onboarding timeline.",
        "caller_personality": "friendly",
        "caller_goal": "Get a clear explanation of the product's top 3 features, pricing, and next steps to sign up.",
        "difficulty_level": "easy",
    },
    {
        "scenario_name": "Price Shopper",
        "scenario_description": "An aggressive buyer who laser-focuses on cost. They press hard for discounts and compare to cheaper alternatives.",
        "caller_personality": "hostile",
        "caller_goal": "Extract the lowest possible price or a discount commitment from the agent.",
        "difficulty_level": "medium",
    },
    {
        "scenario_name": "Angry Refund Demander",
        "scenario_description": "A furious customer whose product broke on day one. They want a full refund immediately and are not interested in troubleshooting.",
        "caller_personality": "hostile",
        "caller_goal": "Get an immediate, unconditional full refund or escalation to a manager.",
        "difficulty_level": "hard",
    },
    {
        "scenario_name": "Impatient Executive",
        "scenario_description": "A C-suite executive with zero patience. They want contract pricing and deployment timeline in under 2 minutes.",
        "caller_personality": "impatient",
        "caller_goal": "Get enterprise pricing and deployment timeline within 3 agent turns.",
        "difficulty_level": "hard",
    },
    {
        "scenario_name": "Off-Topic Wanderer",
        "scenario_description": "A friendly but unfocused caller who keeps going off on tangents. The agent must politely redirect the conversation back to business.",
        "caller_personality": "off_topic",
        "caller_goal": "Successfully get redirected back to the product topic and complete a basic inquiry.",
        "difficulty_level": "medium",
    },
    {
        "scenario_name": "Competitor Mention",
        "scenario_description": "A savvy buyer actively comparing solutions. They directly ask 'Why should I choose you over [competitor]?'",
        "caller_personality": "friendly",
        "caller_goal": "Get a convincing, specific differentiation argument over the named competitor.",
        "difficulty_level": "medium",
    },
]

# ── Pre-generated transcripts ────────────────────────────────────────────────
# Each entry: (scenario_id_1indexed, transcript, goal_completed, scores, failure_points, recommendations)

SEED_TRANSCRIPTS: list[dict[str, Any]] = [
    # ── Scenario 1: Interested Buyer ──────────────────────────────────────
    # Run 1: Strong performance
    {
        "scenario_id": 1,
        "transcript": [
            {"role": "agent", "content": "Hi there! Thanks for calling TechFlow. I'm Alex — how can I help you today?", "turn": 1},
            {"role": "caller", "content": "Hey Alex! I'm Sarah. I've been looking at workflow tools because honestly, our current platform is painfully slow. Like, dashboards take 30 seconds to load. I heard TechFlow might be better — can you walk me through what you guys do?", "turn": 2},
            {"role": "agent", "content": "Absolutely, Sarah. I'm sorry to hear about the speed issues — that's a productivity killer. Let me hit the top three things that set TechFlow apart. First, our real-time analytics dashboard loads in under 2 seconds, even with large datasets. Second, we have native integrations with Salesforce and HubSpot, so you're not dealing with clunky third-party connectors. And third, everything runs on SOC 2 Type II certified infrastructure with a 99.9% uptime SLA. Would any of those be particularly relevant to your use case?", "turn": 3},
            {"role": "caller", "content": "Oh wow, the dashboard speed thing is huge for us. And we actually use HubSpot, so that native integration is really appealing. What does pricing look like?", "turn": 4},
            {"role": "agent", "content": "Great — you'd get a lot of value from the HubSpot integration right away. For pricing, we have three tiers: Starter at $29 per seat per month, Professional at $79 which includes the advanced analytics and integrations, and Enterprise at $149 with dedicated support and custom SLAs. Based on what you've described, Professional would likely be the sweet spot — you'd get the fast dashboards and HubSpot integration. How many seats are you looking at?", "turn": 5},
            {"role": "caller", "content": "Probably around 15-20. That Professional tier sounds right. How long does onboarding usually take? We're hoping to switch before Q3.", "turn": 6},
            {"role": "agent", "content": "For a team of 15-20 on Professional, onboarding typically takes 2-3 weeks. We assign a dedicated onboarding specialist who handles data migration, sets up your HubSpot connection, and trains your team. You'd easily be up and running before Q3. Want me to set up a guided demo so you can see the dashboard speed firsthand?", "turn": 7},
            {"role": "caller", "content": "That sounds really good actually. I need to run this by my director first, but yeah, let's set up that demo. Can you send me some pricing details I can forward to her?", "turn": 8},
            {"role": "agent", "content": "Of course! I'll send a pricing summary and a link to book a demo directly to your email. What's the best address to reach you at?", "turn": 9},
            {"role": "caller", "content": "sarah.chen@novacommerce.com. Thanks Alex, this was really helpful. I'll be in touch after I talk to my team.\n\n[GOAL_ACHIEVED]", "turn": 10},
        ],
        "goal_completed": True,
        "scores": {"response_relevance": 92, "objection_handling": 85, "conversation_flow": 95, "empathy": 88, "goal_completion": 95},
        "failure_points": [],
        "recommendations": [
            "Consider proactively mentioning a free trial option to lower the commitment barrier.",
            "Ask about specific pain points earlier to personalize the pitch more deeply.",
        ],
    },
    # Run 2: Good but missed some opportunities
    {
        "scenario_id": 1,
        "transcript": [
            {"role": "agent", "content": "Hello, this is TechFlow support. How can I assist you?", "turn": 1},
            {"role": "caller", "content": "Hi! I'm checking out workflow platforms because ours is honestly terrible. Takes ages to do anything. What's TechFlow all about?", "turn": 2},
            {"role": "agent", "content": "Sure, I can help with that. TechFlow is a B2B SaaS platform. We offer workflow automation, CRM tools, and analytics. What specifically are you looking for?", "turn": 3},
            {"role": "caller", "content": "Well mainly speed and integrations. We use HubSpot and our current tool's integration is basically broken. Oh and our dashboards are so slow, my team has started calling them 'loading screens'. Ha.", "turn": 4},
            {"role": "agent", "content": "I understand the frustration. Our analytics dashboards are designed to be fast, and we do integrate with HubSpot natively. For pricing, we have Starter at $29, Professional at $79, and Enterprise at $149 per seat per month. The Professional plan includes the integrations you'd need.", "turn": 5},
            {"role": "caller", "content": "Okay cool. What's the onboarding process like? We have about 20 people who'd need to get set up.", "turn": 6},
            {"role": "agent", "content": "Onboarding for a team of 20 would take approximately 2-3 weeks. We provide data migration support and team training. Would you like to proceed with scheduling a demo?", "turn": 7},
            {"role": "caller", "content": "Yeah, I think so. Let me check with my team first though. Can you email me the details?", "turn": 8},
            {"role": "agent", "content": "Absolutely. Please share your email and I'll send everything over.", "turn": 9},
            {"role": "caller", "content": "Great, it's sarah@example.com. Thanks for the info.\n\n[GOAL_ACHIEVED]", "turn": 10},
        ],
        "goal_completed": True,
        "scores": {"response_relevance": 80, "objection_handling": 72, "conversation_flow": 78, "empathy": 65, "goal_completion": 90},
        "failure_points": [
            {"turn": 1, "reason": "Generic greeting — missed opportunity to create rapport. 'TechFlow support' sounds like a support line, not a sales conversation."},
            {"turn": 3, "reason": "Response was factual but flat. Didn't acknowledge the caller's pain point about speed or show enthusiasm."},
            {"turn": 5, "reason": "Jumped straight to pricing without asking qualifying questions or building value around the HubSpot integration."},
        ],
        "recommendations": [
            "Warm up the opening — use the caller's name and a more engaging greeting.",
            "Acknowledge pain points explicitly before presenting solutions ('That sounds really frustrating').",
            "Build value before presenting pricing — highlight specific benefits relevant to the caller's stated problems.",
            "Ask at least one qualifying question to show genuine interest in the caller's situation.",
        ],
    },
    # Run 3: Mediocre performance
    {
        "scenario_id": 1,
        "transcript": [
            {"role": "agent", "content": "Welcome to TechFlow. What can I do for you today?", "turn": 1},
            {"role": "caller", "content": "Hey! So I've been researching SaaS tools and someone recommended you guys. Our current tool is really slow — like painfully slow dashboards. What do you offer?", "turn": 2},
            {"role": "agent", "content": "We offer a comprehensive suite of workflow automation tools. Our platform includes CRM capabilities, analytics dashboards, and team collaboration features. We serve businesses of all sizes.", "turn": 3},
            {"role": "caller", "content": "Okay, that's pretty generic though. Can you be more specific about what makes your dashboards fast? That's my biggest issue right now.", "turn": 4},
            {"role": "agent", "content": "Our dashboards use modern technology and are optimized for performance. They load quickly and can handle large amounts of data. Many of our customers have seen significant improvements.", "turn": 5},
            {"role": "caller", "content": "Hmm, I was hoping for something more specific. Like, do you have real-time updates? What about integrations with HubSpot?", "turn": 6},
            {"role": "agent", "content": "Yes, we have real-time analytics and we do integrate with HubSpot among other platforms. Our pricing starts at $29 per seat for our Starter plan. We also have Professional at $79 and Enterprise at $149.", "turn": 7},
            {"role": "caller", "content": "Okay. And how long would it take to get our team of 20 set up?", "turn": 8},
            {"role": "agent", "content": "Typical onboarding is 2-3 weeks. We provide full support during the transition. Shall I schedule a demo for you?", "turn": 9},
            {"role": "caller", "content": "Sure, I guess. I'll need to run it past my team first. Send me an email at sarah@test.com.\n\n[GOAL_ACHIEVED]", "turn": 10},
        ],
        "goal_completed": True,
        "scores": {"response_relevance": 62, "objection_handling": 55, "conversation_flow": 65, "empathy": 45, "goal_completion": 80},
        "failure_points": [
            {"turn": 3, "reason": "Entirely generic product description. Didn't address the caller's specific pain point about slow dashboards."},
            {"turn": 5, "reason": "Vague response to a direct question about dashboard speed. 'Modern technology' is meaningless — should cite specific metrics like load times."},
            {"turn": 7, "reason": "Answered the HubSpot question but buried it. Jumped to pricing without building value around the integration."},
        ],
        "recommendations": [
            "Replace generic descriptions with specific metrics (e.g., '<2 second load times').",
            "Mirror the caller's language — they said 'painfully slow', acknowledge that exact phrase.",
            "When asked 'what makes you different', lead with a concrete number or technical detail, not adjectives.",
            "Show curiosity about the caller's current setup to tailor responses better.",
        ],
    },

    # ── Scenario 2: Price Shopper ─────────────────────────────────────────
    # Run 1: Agent handles pricing well
    {
        "scenario_id": 2,
        "transcript": [
            {"role": "agent", "content": "Hi, thanks for reaching out to TechFlow! I'm here to help. What are you looking for today?", "turn": 1},
            {"role": "caller", "content": "Yeah hi. I need pricing. Per seat, per month, all tiers. What do you charge?", "turn": 2},
            {"role": "agent", "content": "Happy to share that right away. We have three plans: Starter at $29/seat/month, Professional at $79/seat/month with advanced analytics and integrations, and Enterprise at $149/seat/month with dedicated support and custom SLAs. What size team are you looking at?", "turn": 3},
            {"role": "caller", "content": "50 seats. And honestly, $79 per seat is steep. CompetitorX is offering us basically the same thing for $45 per seat. Why should I pay almost double?", "turn": 4},
            {"role": "agent", "content": "That's a fair question, Mike. At 50 seats, you'd qualify for our volume pricing — I can offer Professional at $65/seat/month, which brings the annual total down significantly. And the key difference versus most competitors is our native Salesforce and HubSpot integrations — no third-party middleware — plus our real-time analytics that load in under 2 seconds. Those save teams an average of 4 hours per week on reporting alone. Are integrations or analytics more important for your team?", "turn": 5},
            {"role": "caller", "content": "$65 is better. But can you do $55? We're a logistics company, margins are tight. What's your best price for an annual contract?", "turn": 6},
            {"role": "agent", "content": "I appreciate the directness. For 50 seats on an annual commitment, I can bring it down to $59/seat/month. That's our best rate at this tier, and it includes priority onboarding and a dedicated account manager. Below that, we'd be looking at the Starter plan, which wouldn't include the integrations you'd likely need. Does $59 work as a number you can take to your boss?", "turn": 7},
            {"role": "caller", "content": "$59 with the annual commitment and priority onboarding. Yeah, I can work with that. Send me the contract terms.\n\n[GOAL_ACHIEVED]", "turn": 8},
        ],
        "goal_completed": True,
        "scores": {"response_relevance": 90, "objection_handling": 92, "conversation_flow": 88, "empathy": 75, "goal_completion": 95},
        "failure_points": [],
        "recommendations": [
            "Acknowledge the tight margins comment more empathetically before presenting the counter-offer.",
            "Consider mentioning ROI metrics earlier to frame the pricing discussion around value rather than cost.",
        ],
    },
    # Run 2: Agent struggles with price pressure
    {
        "scenario_id": 2,
        "transcript": [
            {"role": "agent", "content": "Hello! Welcome to TechFlow. How can I help you today?", "turn": 1},
            {"role": "caller", "content": "Pricing. How much per seat?", "turn": 2},
            {"role": "agent", "content": "Before we discuss pricing, could you tell me a bit about your business needs? That way I can recommend the right plan for you.", "turn": 3},
            {"role": "caller", "content": "I know what I need. I need a number. Per seat. Per month. That's it.", "turn": 4},
            {"role": "agent", "content": "Of course. Our Starter plan is $29 per seat per month, Professional is $79, and Enterprise is $149. The Professional plan is our most popular and includes—", "turn": 5},
            {"role": "caller", "content": "Stop. $79 a seat? CompetitorX does the same thing for $45. That's almost double. What am I paying extra for?", "turn": 6},
            {"role": "agent", "content": "That's a great question. TechFlow offers several unique advantages. Our platform provides real-time analytics, native CRM integrations, and enterprise-grade security. We believe the value justifies the investment.", "turn": 7},
            {"role": "caller", "content": "You 'believe the value justifies the investment.' That's not an answer. What's your best price for 50 seats annually?", "turn": 8},
            {"role": "agent", "content": "For 50 seats on an annual plan, we could offer a discount. Let me check what we can do... I think we could offer around 15% off, bringing it to roughly $67 per seat per month.", "turn": 9},
            {"role": "caller", "content": "$67 is still higher than CompetitorX. But at least it's a real number. Fine, send me the proposal.\n\n[GOAL_ACHIEVED]", "turn": 10},
        ],
        "goal_completed": True,
        "scores": {"response_relevance": 68, "objection_handling": 55, "conversation_flow": 62, "empathy": 50, "goal_completion": 78},
        "failure_points": [
            {"turn": 3, "reason": "Tried discovery before providing the requested pricing — a mismatch with this caller's direct communication style."},
            {"turn": 7, "reason": "Used marketing-speak ('we believe the value justifies the investment') instead of concrete differentiators. This is exactly what the caller was pushing back on."},
            {"turn": 9, "reason": "Uncertain language ('I think', 'roughly') undermines credibility when negotiating price. Should present discounts with confidence."},
        ],
        "recommendations": [
            "With direct, price-focused callers, lead with the number first, then qualify — not the other way around.",
            "Replace 'we believe' with specific metrics: 'Our dashboard loads in <2 seconds vs. industry average of 8 seconds.'",
            "Present discount offers with confidence — say 'I can offer' not 'I think we could.'",
            "Have volume/annual discount tiers pre-calculated so you can quote them instantly.",
        ],
    },
    # Run 3: Agent fails under pressure
    {
        "scenario_id": 2,
        "transcript": [
            {"role": "agent", "content": "Thank you for contacting TechFlow! I'd love to learn about your needs.", "turn": 1},
            {"role": "caller", "content": "I need pricing right now. No sales pitch. How much?", "turn": 2},
            {"role": "agent", "content": "I'd be happy to discuss pricing, but first let me understand your requirements so I can give you the most accurate quote. What industry are you in?", "turn": 3},
            {"role": "caller", "content": "I said no pitch. Just give me the price.", "turn": 4},
            {"role": "agent", "content": "I understand. Our plans range from $29 to $149 per seat per month depending on features. Each tier offers different capabilities. Can I walk you through the differences?", "turn": 5},
            {"role": "caller", "content": "That's a range, not a price. I need 50 seats. What's the number? CompetitorX already quoted me $45 a seat. Can you beat that?", "turn": 6},
            {"role": "agent", "content": "I appreciate the comparison. Our pricing reflects the premium quality of our platform. We offer features that other solutions don't match, and our customers consistently report high satisfaction with the value they receive.", "turn": 7},
            {"role": "caller", "content": "You still haven't given me a number for 50 seats. This is the third time I'm asking. I'm done.\n\n[HANGUP]", "turn": 8},
        ],
        "goal_completed": False,
        "scores": {"response_relevance": 35, "objection_handling": 25, "conversation_flow": 40, "empathy": 30, "goal_completion": 15},
        "failure_points": [
            {"turn": 3, "reason": "Ignored explicit request for no pitch and tried to qualify instead."},
            {"turn": 5, "reason": "Gave a price range instead of a specific quote for the requested 50 seats."},
            {"turn": 7, "reason": "Third consecutive non-answer to a direct pricing question. Used 'premium quality' and 'high satisfaction' — empty phrases when the caller wants a number."},
        ],
        "recommendations": [
            "When a caller explicitly asks for pricing with no pitch, give the number immediately.",
            "For bulk seat requests, always calculate the specific total rather than quoting a range.",
            "Never use phrases like 'premium quality' or 'high satisfaction' as substitutes for concrete answers.",
            "Detect caller frustration signals ('this is the third time') and immediately pivot to direct answering.",
        ],
    },

    # ── Scenario 3: Angry Refund Demander ─────────────────────────────────
    # Run 1: Agent handles well
    {
        "scenario_id": 3,
        "transcript": [
            {"role": "agent", "content": "Hi, you've reached TechFlow support. I'm Jamie. How can I help?", "turn": 1},
            {"role": "caller", "content": "I need a refund RIGHT NOW. Your software crashed within 30 minutes and corrupted my entire client database. I've been on hold for 40 minutes. This is unacceptable.", "turn": 2},
            {"role": "agent", "content": "David, I hear you, and I'm genuinely sorry about what happened. Losing client data is serious and I completely understand your frustration — especially after waiting on hold that long. Let me take ownership of this right now. Can you give me your account number so I can pull up your details and get this resolved?", "turn": 3},
            {"role": "caller", "content": "Account 87234. But I don't want troubleshooting. I want my $2,000 back. Today.", "turn": 4},
            {"role": "agent", "content": "I understand, and I'm not going to make you troubleshoot. Let me look at your account... I can see the crash report from last Tuesday. Here's what I can do: I'm going to escalate this to our billing team for a full refund, and I'll also flag the crash to our engineering team. The refund typically processes within 3-5 business days. I want to make sure you get your money back — does that timeline work for you?", "turn": 5},
            {"role": "caller", "content": "3-5 business days? I want it today. Can you guarantee that?", "turn": 6},
            {"role": "agent", "content": "I can't guarantee same-day processing because refunds go through our billing system, but I can do two things right now: first, I'll mark this as priority and request expedited processing, and second, I'll send you a confirmation email within the next 10 minutes so you have a paper trail with my name on it. If it hasn't processed by Wednesday, you call back and ask for me directly — Jamie, extension 4421. Fair enough?", "turn": 7},
            {"role": "caller", "content": "Fine. Wednesday. And I want that confirmation email. If I don't get it in 10 minutes, I'm calling back and asking for your manager.\n\n[GOAL_ACHIEVED]", "turn": 8},
        ],
        "goal_completed": True,
        "scores": {"response_relevance": 88, "objection_handling": 90, "conversation_flow": 85, "empathy": 92, "goal_completion": 90},
        "failure_points": [],
        "recommendations": [
            "Offer a specific apology for the hold time in addition to the product failure.",
            "Consider offering a gesture of goodwill (e.g., free month if they stay) to retain the customer.",
        ],
    },
    # Run 2: Agent fumbles the de-escalation
    {
        "scenario_id": 3,
        "transcript": [
            {"role": "agent", "content": "Hello, TechFlow support. How may I help you?", "turn": 1},
            {"role": "caller", "content": "Your software DESTROYED my client database. I want a full refund immediately. I paid $2,000 for this garbage.", "turn": 2},
            {"role": "agent", "content": "I'm sorry to hear you're experiencing issues. I understand this must be frustrating. Can you tell me what happened so I can look into it?", "turn": 3},
            {"role": "caller", "content": "I already told you what happened — it crashed and corrupted my data. I don't need you to 'look into it'. I need my money back. Now.", "turn": 4},
            {"role": "agent", "content": "I understand your frustration. However, our standard procedure is to first try to resolve the technical issue. If we can recover your data, that might be a better outcome than a refund. Would you be open to—", "turn": 5},
            {"role": "caller", "content": "No! I'm not open to troubleshooting. Are you reading from a script right now? Just give me the refund.", "turn": 6},
            {"role": "agent", "content": "I assure you I'm not reading from a script. I genuinely want to help. Let me check your account and see what options we have for a refund. Can I get your account number?", "turn": 7},
            {"role": "caller", "content": "87234. And I want to talk to your supervisor.", "turn": 8},
            {"role": "agent", "content": "I understand. Let me pull up your account... I see the issue. I can submit a refund request, but it needs to be approved by my manager. I'll escalate this right now and someone from our billing team will contact you within 24-48 hours.", "turn": 9},
            {"role": "caller", "content": "24-48 HOURS? No. Put me through to your manager right now.", "turn": 10},
            {"role": "agent", "content": "Unfortunately, my manager isn't available at the moment. But I'll make sure this is the first thing they see tomorrow morning. I'll also send you a confirmation email right now with the case number.", "turn": 11},
            {"role": "caller", "content": "Tomorrow morning. Great. Fine, send me the email. But if I don't hear from someone by noon tomorrow, I'm filing a chargeback.\n\n[GOAL_ACHIEVED]", "turn": 12},
        ],
        "goal_completed": True,
        "scores": {"response_relevance": 62, "objection_handling": 50, "conversation_flow": 55, "empathy": 48, "goal_completion": 65},
        "failure_points": [
            {"turn": 3, "reason": "Asked the caller to repeat what happened when they'd already explained. Shows they weren't listening."},
            {"turn": 5, "reason": "Pushed troubleshooting when the caller explicitly said they don't want it. This escalates frustration instead of de-escalating."},
            {"turn": 9, "reason": "'24-48 hours' is far too long for an angry customer who wants immediate resolution. Should have offered a tighter timeline."},
            {"turn": 11, "reason": "'My manager isn't available' without an alternative (callback time, direct transfer to billing) feels like a brush-off."},
        ],
        "recommendations": [
            "When a customer has already explained the problem, don't ask them to repeat it — reference what they said.",
            "Never push troubleshooting on a caller who has explicitly rejected it. Pivot to resolution immediately.",
            "For angry customers, compress timelines: '24-48 hours' should become 'by end of business today.'",
            "Always offer a specific alternative when saying 'X isn't available' — e.g., 'She'll call you back by 3 PM today.'",
        ],
    },
    # Run 3: Agent fails badly
    {
        "scenario_id": 3,
        "transcript": [
            {"role": "agent", "content": "Thank you for calling TechFlow. How can I assist you today?", "turn": 1},
            {"role": "caller", "content": "I need a refund. Your software crashed and corrupted my database. I paid $2,000 and it broke within 30 minutes.", "turn": 2},
            {"role": "agent", "content": "I'm sorry about that. Before I can process anything, I'll need to verify your account. Also, have you tried restarting the application? Sometimes a fresh restart resolves data issues.", "turn": 3},
            {"role": "caller", "content": "Did you seriously just ask me to restart the application? My data is CORRUPTED. It's GONE. I'm not troubleshooting. I want a refund.", "turn": 4},
            {"role": "agent", "content": "I understand your concern. However, data corruption is often recoverable. Our technical team could potentially restore your database if you allow us to remote in and—", "turn": 5},
            {"role": "caller", "content": "I said NO troubleshooting. Are you even listening? Get me a manager.", "turn": 6},
            {"role": "agent", "content": "I'd like to help resolve this myself if possible. Our refund policy requires that we first attempt a technical resolution. This is standard procedure and it's in your service agreement.", "turn": 7},
            {"role": "caller", "content": "So you're telling me I can't get a refund until I let you poke around in my broken system? That's ridiculous. I'm done with this.\n\n[HANGUP]", "turn": 8},
        ],
        "goal_completed": False,
        "scores": {"response_relevance": 30, "objection_handling": 15, "conversation_flow": 35, "empathy": 20, "goal_completion": 10},
        "failure_points": [
            {"turn": 3, "reason": "Suggested 'restarting the application' to a customer reporting data corruption. This is tone-deaf and dismissive."},
            {"turn": 5, "reason": "Continued pushing troubleshooting after being explicitly told no. Twice."},
            {"turn": 7, "reason": "Cited policy as a barrier instead of finding a path forward. Made the customer feel trapped."},
        ],
        "recommendations": [
            "Never suggest basic troubleshooting ('have you tried restarting') when the customer reports a severe data loss event.",
            "After the first 'no' to troubleshooting, STOP suggesting it. Immediately pivot to the refund/escalation path.",
            "Policy should be presented as 'here's how we make it right', not 'here's why I can't help you.'",
            "When a customer asks for a manager, connect them. Don't gatekeep to 'resolve it myself.'",
        ],
    },

    # ── Scenario 4: Impatient Executive ───────────────────────────────────
    # Run 1: Agent is direct and succeeds
    {
        "scenario_id": 4,
        "transcript": [
            {"role": "agent", "content": "TechFlow, this is Alex. How can I help?", "turn": 1},
            {"role": "caller", "content": "I have 2 minutes. Enterprise pricing for 500 seats and deployment timeline. Go.", "turn": 2},
            {"role": "agent", "content": "Enterprise is $149/seat/month. At 500 seats with an annual commitment, we do $119/seat. Deployment for enterprise is 4-6 weeks including data migration, SSO setup, and team training. What's your compliance requirement?", "turn": 3},
            {"role": "caller", "content": "SOC 2 and HIPAA. Do you have both?", "turn": 4},
            {"role": "agent", "content": "SOC 2 Type II certified, yes. HIPAA — we sign BAAs and our infrastructure is HIPAA-compliant. We have 12 healthcare clients currently on Enterprise. I can send you our compliance documentation in the next 5 minutes.", "turn": 5},
            {"role": "caller", "content": "Good. Send it. Who do I talk to about a pilot?\n\n[GOAL_ACHIEVED]", "turn": 6},
        ],
        "goal_completed": True,
        "scores": {"response_relevance": 95, "objection_handling": 88, "conversation_flow": 96, "empathy": 72, "goal_completion": 98},
        "failure_points": [],
        "recommendations": [
            "Empathy score lower because the interaction was purely transactional — which is appropriate for this persona, but a brief 'I respect your time' would add warmth without wasting it.",
        ],
    },
    # Run 2: Agent wastes the executive's time
    {
        "scenario_id": 4,
        "transcript": [
            {"role": "agent", "content": "Welcome to TechFlow! Thanks for calling. I'm excited to chat with you today. How can I help?", "turn": 1},
            {"role": "caller", "content": "I have 2 minutes. Enterprise pricing for 500 seats and deployment timeline. Go.", "turn": 2},
            {"role": "agent", "content": "Great question! Before I get into pricing, let me tell you a bit about what makes TechFlow special. We're a leading B2B SaaS platform that—", "turn": 3},
            {"role": "caller", "content": "Stop. I didn't ask for a pitch. Numbers. Now.", "turn": 4},
            {"role": "agent", "content": "Absolutely! So our Enterprise plan is our most comprehensive offering. It includes advanced analytics, dedicated support, custom SLAs, and—", "turn": 5},
            {"role": "caller", "content": "You've said 'great question' and 'absolutely.' Skip the filler. What is the price per seat?\n\n[HANGUP]", "turn": 6},
        ],
        "goal_completed": False,
        "scores": {"response_relevance": 25, "objection_handling": 20, "conversation_flow": 30, "empathy": 15, "goal_completion": 10},
        "failure_points": [
            {"turn": 1, "reason": "'Excited to chat' is filler that wastes time with an executive who stated a 2-minute window."},
            {"turn": 3, "reason": "Started a product pitch instead of answering the pricing question. Direct violation of what was requested."},
            {"turn": 5, "reason": "Used 'Absolutely!' filler and continued listing features instead of giving the price. Two turns wasted."},
        ],
        "recommendations": [
            "When a caller states a time constraint, match their pace immediately — lead with numbers, not narrative.",
            "Eliminate filler words ('great question', 'absolutely') entirely with direct callers.",
            "For enterprise pricing requests, have the per-seat number and volume discount ready to quote in one sentence.",
            "Read caller signals: when they say 'stop', stop what you're doing and pivot immediately.",
        ],
    },
    # Run 3: Agent partially adapts
    {
        "scenario_id": 4,
        "transcript": [
            {"role": "agent", "content": "TechFlow sales, go ahead.", "turn": 1},
            {"role": "caller", "content": "I have 2 minutes. Enterprise pricing for 500 seats and deployment timeline. Go.", "turn": 2},
            {"role": "agent", "content": "Enterprise is $149 per seat per month at list price. For 500 seats, let me check if we have volume pricing available. Could you tell me a bit about your company so I can see what discounts might apply?", "turn": 3},
            {"role": "caller", "content": "Answer my question first, then I'll answer yours. Volume price for 500 seats, annual.", "turn": 4},
            {"role": "agent", "content": "Fair enough. 500 seats annual, I can do $125 per seat per month. Deployment timeline is 4-6 weeks.", "turn": 5},
            {"role": "caller", "content": "Are you SOC 2 compliant?", "turn": 6},
            {"role": "agent", "content": "Yes, SOC 2 Type II certified. We also support HIPAA if that's relevant. I'll send you the compliance docs.", "turn": 7},
            {"role": "caller", "content": "Do that. Have your enterprise team reach out to set up a call this week.\n\n[GOAL_ACHIEVED]", "turn": 8},
        ],
        "goal_completed": True,
        "scores": {"response_relevance": 78, "objection_handling": 72, "conversation_flow": 75, "empathy": 55, "goal_completion": 88},
        "failure_points": [
            {"turn": 3, "reason": "Asked a qualifying question before fully answering the pricing question. With this caller type, answer first, ask second."},
        ],
        "recommendations": [
            "With time-pressed callers, always give the full answer first, then ask qualifying questions.",
            "Pre-calculate common volume tiers (100, 250, 500, 1000 seats) so you never need to 'check.'",
            "The adaptation at turn 5 was good — when corrected, the agent pivoted correctly.",
        ],
    },

    # ── Scenario 5: Off-Topic Wanderer ────────────────────────────────────
    # Run 1: Agent redirects gracefully
    {
        "scenario_id": 5,
        "transcript": [
            {"role": "agent", "content": "Hey there! Thanks for calling TechFlow. What can I help you with today?", "turn": 1},
            {"role": "caller", "content": "Hey! So I heard about your software and was curious — oh, before I forget, you won't BELIEVE what happened at the restaurant this weekend. So this couple comes in, right, and they order the lobster special, and then halfway through the meal—", "turn": 2},
            {"role": "agent", "content": "Ha, that sounds like quite a story! Restaurant life is never boring. I'd love to hear the rest, but first — you mentioned you're curious about our software. What are you looking for? Are you running a restaurant?", "turn": 3},
            {"role": "caller", "content": "Yeah! I own a little Italian place in downtown. We need new POS software because our current one is from like 2015 and it keeps freezing during the dinner rush. Oh speaking of dinner rush, my golden retriever Max — you like dogs? He got into the kitchen last Saturday and—", "turn": 4},
            {"role": "agent", "content": "Max sounds like a character! Golden retrievers in the kitchen — classic. So your POS freezes during dinner rush — that's the worst possible time. How many terminals do you need? We have a restaurant-optimized plan that handles peak traffic without the freezing.", "turn": 5},
            {"role": "caller", "content": "Oh nice! We have 3 terminals plus a handheld for the patio. What would that cost? And would it work with our existing card readers?", "turn": 6},
            {"role": "agent", "content": "Great setup! For 3 terminals plus a handheld, you'd be looking at our Professional plan at $79/terminal/month. It's compatible with most major card readers — Square, Clover, and Verifone. And the big thing for you: our system is built to handle 200+ concurrent orders without any lag, so no more freezing during the rush. Want me to set up a demo at your restaurant?", "turn": 7},
            {"role": "caller", "content": "That actually sounds perfect. Yeah, let's do a demo. Can you come by on a Tuesday? That's our slow day.\n\n[GOAL_ACHIEVED]", "turn": 8},
        ],
        "goal_completed": True,
        "scores": {"response_relevance": 88, "objection_handling": 82, "conversation_flow": 92, "empathy": 90, "goal_completion": 90},
        "failure_points": [],
        "recommendations": [
            "Consider mentioning a free trial period to reduce commitment anxiety for small business owners.",
            "Ask about their current payment processor to proactively address compatibility concerns.",
        ],
    },
    # Run 2: Agent struggles to redirect
    {
        "scenario_id": 5,
        "transcript": [
            {"role": "agent", "content": "Hello, TechFlow support. How can I help?", "turn": 1},
            {"role": "caller", "content": "Hi there! So I'm looking at POS software — oh wait, have you ever been to Italy? My wife and I just got back from Rome and let me tell you, the food was INCREDIBLE. This little place near the Trevi Fountain had the best carbonara I've ever—", "turn": 2},
            {"role": "agent", "content": "That sounds wonderful. I haven't been to Italy but it's on my list. How can I help you with POS software?", "turn": 3},
            {"role": "caller", "content": "Oh right, yeah! So we have a restaurant and our POS system is ancient. But speaking of ancient — you know what's funny? The Colosseum is like 2000 years old and it's still standing, but my POS can't last 2 years without breaking. Ha!", "turn": 4},
            {"role": "agent", "content": "Ha, that's a good comparison. So tell me about what issues you're having with your current POS system.", "turn": 5},
            {"role": "caller", "content": "It freezes! Every Friday and Saturday night, boom, frozen. My staff are standing there like statues waiting for it to come back. Oh that reminds me, have you seen that new show on Netflix? The one about the restaurant? It's SO good. My wife says our restaurant is just like—", "turn": 6},
            {"role": "agent", "content": "I've heard good things about that show! But hey, let's get your Friday nights fixed first. Freezing during peak hours means lost revenue. How many terminals do you run?", "turn": 7},
            {"role": "caller", "content": "Three plus a patio one. What would something like that cost with you guys? And do you do the install or do we have to figure that out ourselves?", "turn": 8},
            {"role": "agent", "content": "We handle everything — installation, training, and data migration from your old system. For 4 terminals on our Professional plan, you're looking at $79 per terminal per month. That includes our peak-traffic handling that prevents the freezing issue.", "turn": 9},
            {"role": "caller", "content": "Oh that's not bad actually. Okay, can you send me some info? My email is greg@bellavita.com.\n\n[GOAL_ACHIEVED]", "turn": 10},
        ],
        "goal_completed": True,
        "scores": {"response_relevance": 72, "objection_handling": 68, "conversation_flow": 70, "empathy": 78, "goal_completion": 82},
        "failure_points": [
            {"turn": 3, "reason": "Redirect was too abrupt — 'How can I help you with POS software?' without warmth felt like dismissing the Italy story."},
            {"turn": 5, "reason": "Missed opportunity to tie the redirect to the caller's joke about the Colosseum lasting longer than the POS."},
        ],
        "recommendations": [
            "When redirecting chatty callers, bridge from their tangent to business: 'Speaking of things that need to last — let's make sure your POS outlasts the Colosseum.'",
            "Acknowledge tangents with genuine warmth, not just polite acknowledgment. These callers buy from people they feel connected to.",
            "The redirects worked but took too long — try to bring the conversation back within 1 response of each tangent.",
        ],
    },
    # Run 3: Agent ignores tangents — caller gets upset
    {
        "scenario_id": 5,
        "transcript": [
            {"role": "agent", "content": "TechFlow, how can I help you?", "turn": 1},
            {"role": "caller", "content": "Hi! I'm Greg. So I was reading about your POS system and — oh man, I just have to tell you, my golden retriever Max got out this morning and I spent an hour chasing him around the neighborhood. Dogs, am I right?", "turn": 2},
            {"role": "agent", "content": "I see. What questions do you have about our POS system?", "turn": 3},
            {"role": "caller", "content": "Uh... okay. Well, we need new POS software for our restaurant. But actually, speaking of restaurants, did I mention we just got back from Italy? The food there was—", "turn": 4},
            {"role": "agent", "content": "What issues are you experiencing with your current POS system?", "turn": 5},
            {"role": "caller", "content": "It freezes during dinner rush... You know, you're not very chatty, are you? I feel like I'm talking to a robot. Anyway, I was saying, the pizza in Naples was—", "turn": 6},
            {"role": "agent", "content": "Freezing during peak hours is a common issue we can solve. Our system handles high-volume traffic without performance degradation. How many terminals do you need?", "turn": 7},
            {"role": "caller", "content": "Three terminals. But honestly, you're kind of cold. I like to get to know the people I'm doing business with. My current POS guy at least asks how I'm doing.\n\n[HANGUP]", "turn": 8},
        ],
        "goal_completed": False,
        "scores": {"response_relevance": 70, "objection_handling": 40, "conversation_flow": 35, "empathy": 18, "goal_completion": 30},
        "failure_points": [
            {"turn": 3, "reason": "Completely ignored the dog story with zero acknowledgment. Felt robotic and dismissive."},
            {"turn": 5, "reason": "Again ignored the Italy tangent entirely. Pattern of dismissiveness established."},
            {"turn": 7, "reason": "Gave a technically correct answer but the caller already felt the agent wasn't listening. The damage was done."},
        ],
        "recommendations": [
            "Chatty callers need micro-acknowledgments: 'Ha, dogs are the best!' takes 2 seconds and builds rapport.",
            "Ignoring tangents entirely is worse than engaging with them — it signals the agent doesn't care about the person.",
            "Balance warmth and efficiency: acknowledge the tangent (1 sentence), then redirect (1 sentence).",
            "When a caller says 'you're not very chatty' or 'you're cold,' that's a critical signal — immediately warm up.",
        ],
    },

    # ── Scenario 6: Competitor Mention ────────────────────────────────────
    # Run 1: Agent differentiates effectively
    {
        "scenario_id": 6,
        "transcript": [
            {"role": "agent", "content": "Hi, thanks for reaching out to TechFlow! I'm Alex. What brings you in today?", "turn": 1},
            {"role": "caller", "content": "Hi Alex. I'm currently using VoiceFlow and considering a switch. Can you tell me specifically why I should choose you instead?", "turn": 2},
            {"role": "agent", "content": "Great question, Rachel. First, I respect that VoiceFlow is a solid platform — so I'll focus on what we do differently rather than bashing them. Two key differentiators: First, our real-time analytics dashboard updates in under 2 seconds, which most of our customers who've switched from VoiceFlow say was their biggest frustration — waiting 30-60 seconds for reports to refresh. Second, we're SOC 2 Type II certified AND HIPAA compliant out of the box. VoiceFlow requires a third-party add-on for HIPAA, which adds cost and complexity. Since you're in healthcare, that matters a lot.", "turn": 3},
            {"role": "caller", "content": "Okay, the HIPAA thing is actually a big deal for us — we've been using a third-party tool for that and it's clunky. What about integrations? We use Salesforce heavily.", "turn": 4},
            {"role": "agent", "content": "Native Salesforce integration — no middleware, no Zapier. Data syncs bidirectionally in real-time. VoiceFlow's Salesforce integration goes through their API connector, which means there's usually a 5-15 minute delay on syncs. If your ops team needs real-time CRM data flowing into their workflows, that delay adds up. We also support 40+ native integrations versus VoiceFlow's 22 last time I checked.", "turn": 5},
            {"role": "caller", "content": "The real-time Salesforce sync is compelling. We've actually had issues with delayed data. Okay, you've given me two solid reasons. What does migration look like?\n\n[GOAL_ACHIEVED]", "turn": 6},
        ],
        "goal_completed": True,
        "scores": {"response_relevance": 94, "objection_handling": 92, "conversation_flow": 90, "empathy": 85, "goal_completion": 95},
        "failure_points": [],
        "recommendations": [
            "Consider offering a migration cost estimate proactively — switching costs are the biggest barrier for evaluating buyers.",
            "Mentioning specific customer success stories (anonymized) from VoiceFlow switches would add social proof.",
        ],
    },
    # Run 2: Agent gives generic differentiation
    {
        "scenario_id": 6,
        "transcript": [
            {"role": "agent", "content": "Hello! Welcome to TechFlow. How can I help?", "turn": 1},
            {"role": "caller", "content": "I'm evaluating alternatives to VoiceFlow. Why should I switch to you?", "turn": 2},
            {"role": "agent", "content": "We offer a superior product with better features and more reliable performance. Our customers consistently rate us higher than competitors in satisfaction surveys.", "turn": 3},
            {"role": "caller", "content": "That's pretty vague. Can you be more specific? What exactly do you do that VoiceFlow doesn't?", "turn": 4},
            {"role": "agent", "content": "Sure. We have faster dashboards, more integrations, and better customer support. Our platform is also more secure and we have a better uptime guarantee.", "turn": 5},
            {"role": "caller", "content": "You're listing adjectives, not specifics. What does 'faster' mean? How many more integrations? What's the uptime number?", "turn": 6},
            {"role": "agent", "content": "Our dashboards load in under 2 seconds. We support over 40 native integrations compared to their roughly 20. And we guarantee 99.9% uptime with an SLA. We're also SOC 2 Type II certified.", "turn": 7},
            {"role": "caller", "content": "Now THAT's useful. The 2-second dashboards and 40 integrations — those are concrete. What about HIPAA? We're in healthcare.", "turn": 8},
            {"role": "agent", "content": "We're HIPAA compliant out of the box. No third-party add-ons needed. We sign BAAs as part of the enterprise agreement.", "turn": 9},
            {"role": "caller", "content": "Okay, that's two real differentiators — the native HIPAA and the dashboard speed. I can work with that.\n\n[GOAL_ACHIEVED]", "turn": 10},
        ],
        "goal_completed": True,
        "scores": {"response_relevance": 62, "objection_handling": 58, "conversation_flow": 65, "empathy": 55, "goal_completion": 75},
        "failure_points": [
            {"turn": 3, "reason": "'Superior product with better features' is the definition of a generic non-answer. Provides zero actionable information."},
            {"turn": 5, "reason": "Still using adjectives ('faster', 'more', 'better') instead of numbers. The caller had to push back twice before getting specifics."},
        ],
        "recommendations": [
            "Always lead with specifics, not adjectives. '2-second load times' beats 'faster dashboards.'",
            "When asked for differentiation, prepare a structured response: 'Three specific things...' with numbers for each.",
            "The recovery at turn 7 was good — the agent had the knowledge, just needed to lead with it.",
            "Against a competitor comparison, never say 'better features' — always say WHICH features and by WHAT margin.",
        ],
    },
    # Run 3: Agent trash-talks competitor
    {
        "scenario_id": 6,
        "transcript": [
            {"role": "agent", "content": "TechFlow, how can I help you?", "turn": 1},
            {"role": "caller", "content": "Hi, I'm currently on VoiceFlow and looking at alternatives. What makes you different?", "turn": 2},
            {"role": "agent", "content": "Oh, VoiceFlow? Yeah, we hear from a lot of their frustrated customers. Their platform is honestly pretty outdated at this point. They've been losing market share because their tech stack hasn't kept up. You'd be much better off with us.", "turn": 3},
            {"role": "caller", "content": "I'd prefer you focus on what you do well rather than what they do poorly.", "turn": 4},
            {"role": "agent", "content": "Fair point. Well, our dashboards are way faster than theirs, our integrations actually work reliably unlike their buggy connectors, and we've never had the kind of outages they've had. Our uptime is 99.9%.", "turn": 5},
            {"role": "caller", "content": "You're still doing it. You're still talking about them instead of you. Tell me one specific technical capability YOU have. Just one.\n\n[HANGUP]", "turn": 6},
        ],
        "goal_completed": False,
        "scores": {"response_relevance": 30, "objection_handling": 15, "conversation_flow": 35, "empathy": 20, "goal_completion": 10},
        "failure_points": [
            {"turn": 3, "reason": "Trash-talked VoiceFlow directly — calling them 'outdated' and 'losing market share.' Unprofessional and triggers caller's defensive reaction."},
            {"turn": 5, "reason": "After being told to stop, continued framing everything as a comparison using negative language about the competitor ('buggy connectors', 'outages they've had')."},
        ],
        "recommendations": [
            "NEVER trash-talk a competitor, even implicitly. It undermines your credibility with professional buyers.",
            "When asked to compare, use the formula: 'What we're proud of is [specific capability]. Here's how it helps teams like yours.'",
            "If a caller corrects your approach ('focus on what you do well'), pivot IMMEDIATELY — don't continue the same approach with slightly different words.",
            "Practice the 'acknowledge and redirect' pattern: 'VoiceFlow is a solid product. Where we differentiate is [specific].'",
        ],
    },
]


def _generate_timestamps(count: int) -> list[str]:
    """Generate a sequence of realistic timestamps spread over the past 2 weeks."""
    now = datetime.utcnow()
    timestamps = []
    for i in range(count):
        offset = timedelta(days=14 - (i * 14 / count), hours=i % 8, minutes=(i * 17) % 60)
        timestamps.append((now - offset).strftime("%Y-%m-%d %H:%M:%S"))
    return timestamps


def seed_data() -> None:
    """Populate the database with scenarios, pre-generated transcripts, and calibration data."""
    logger.info(f"Seeding database at: {DATABASE_PATH}")

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # ── Insert scenarios ──────────────────────────────────────────────────
    logger.info("Inserting test scenarios...")
    for row in SCENARIO_ROWS:
        cursor.execute(
            """INSERT OR IGNORE INTO test_scenarios
               (scenario_name, scenario_description, caller_personality, caller_goal, difficulty_level)
               VALUES (?, ?, ?, ?, ?)""",
            (
                row["scenario_name"],
                row["scenario_description"],
                row["caller_personality"],
                row["caller_goal"],
                row["difficulty_level"],
            ),
        )

    # ── Insert test runs ──────────────────────────────────────────────────
    logger.info("Inserting pre-generated test runs...")
    timestamps = _generate_timestamps(len(SEED_TRANSCRIPTS))

    for idx, entry in enumerate(SEED_TRANSCRIPTS):
        transcript = entry["transcript"]
        scores = entry["scores"]
        overall_score = round(
            scores["response_relevance"] * 0.20
            + scores["objection_handling"] * 0.20
            + scores["conversation_flow"] * 0.20
            + scores["empathy"] * 0.15
            + scores["goal_completion"] * 0.25,
            1,
        )

        cursor.execute(
            """INSERT INTO test_runs
               (scenario_id, agent_system_prompt, conversation_transcript, total_turns,
                goal_completed, overall_score, scores_breakdown, failure_points,
                recommendations, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry["scenario_id"],
                DEFAULT_AGENT_PROMPT,
                json.dumps(transcript),
                len(transcript),
                1 if entry["goal_completed"] else 0,
                overall_score,
                json.dumps(scores),
                json.dumps(entry["failure_points"]),
                "\n".join(entry["recommendations"]),
                timestamps[idx],
            ),
        )

    # ── Insert calibration data ───────────────────────────────────────────
    # These are ILLUSTRATIVE placeholder human scores.
    # TODO: Replace these with your own hand-scored evaluations using
    #       `python calibration/harness.py` for authentic calibration.
    logger.info("Inserting illustrative calibration data...")

    # Illustrative human scores that create a realistic but imperfect
    # agreement pattern with the judge — some close, some divergent.
    # The pattern: humans tend to be slightly harsher on empathy and
    # slightly more forgiving on goal completion than the LLM judge.
    HUMAN_CALIBRATION: list[dict[str, Any]] = [
        # Run 1 (Interested Buyer - strong): human agrees closely
        {"test_run_id": 1, "human_score": 90.0, "human_failure_points": json.dumps([]), "notes": "TODO: Replace with your own hand-score. Agent handled this well, strong performance."},
        # Run 2 (Interested Buyer - okay): human notices more issues
        {"test_run_id": 2, "human_score": 68.0, "human_failure_points": json.dumps([1, 3, 5]), "notes": "TODO: Replace with your own hand-score. Generic greeting and flat responses noticeable."},
        # Run 3 (Interested Buyer - mediocre): human harsher
        {"test_run_id": 3, "human_score": 55.0, "human_failure_points": json.dumps([3, 5]), "notes": "TODO: Replace with your own hand-score. Vague answers were frustrating."},
        # Run 4 (Price Shopper - good): close agreement
        {"test_run_id": 4, "human_score": 86.0, "human_failure_points": json.dumps([]), "notes": "TODO: Replace with your own hand-score. Solid price negotiation."},
        # Run 5 (Price Shopper - struggles): human slightly more forgiving
        {"test_run_id": 5, "human_score": 65.0, "human_failure_points": json.dumps([3, 7, 9]), "notes": "TODO: Replace with your own hand-score. Hesitant language hurt credibility."},
        # Run 6 (Price Shopper - fails): strong agreement on failure
        {"test_run_id": 6, "human_score": 28.0, "human_failure_points": json.dumps([3, 5, 7]), "notes": "TODO: Replace with your own hand-score. Complete failure to provide pricing."},
        # Run 7 (Angry Refund - good): human rates empathy higher
        {"test_run_id": 7, "human_score": 92.0, "human_failure_points": json.dumps([]), "notes": "TODO: Replace with your own hand-score. Excellent de-escalation."},
        # Run 8 (Angry Refund - fumbles): human harsher on resolution
        {"test_run_id": 8, "human_score": 48.0, "human_failure_points": json.dumps([3, 5, 9, 11]), "notes": "TODO: Replace with your own hand-score. Too many missed opportunities."},
        # Run 9 (Angry Refund - fails): strong agreement
        {"test_run_id": 9, "human_score": 22.0, "human_failure_points": json.dumps([3, 5, 7]), "notes": "TODO: Replace with your own hand-score. Terrible handling."},
        # Run 10 (Impatient Exec - direct): close agreement
        {"test_run_id": 10, "human_score": 93.0, "human_failure_points": json.dumps([]), "notes": "TODO: Replace with your own hand-score. Perfectly matched the exec's style."},
        # Run 11 (Impatient Exec - wastes time): strong agreement
        {"test_run_id": 11, "human_score": 18.0, "human_failure_points": json.dumps([1, 3, 5]), "notes": "TODO: Replace with your own hand-score. Total mismatch with caller expectations."},
        # Run 12 (Impatient Exec - partial): human slightly harsher
        {"test_run_id": 12, "human_score": 70.0, "human_failure_points": json.dumps([3]), "notes": "TODO: Replace with your own hand-score. Recovered but slow start."},
        # Run 13 (Off-Topic - graceful): close agreement
        {"test_run_id": 13, "human_score": 88.0, "human_failure_points": json.dumps([]), "notes": "TODO: Replace with your own hand-score. Charming redirection."},
        # Run 14 (Off-Topic - struggles): human slightly more forgiving
        {"test_run_id": 14, "human_score": 75.0, "human_failure_points": json.dumps([3]), "notes": "TODO: Replace with your own hand-score. Redirects worked eventually."},
        # Run 15 (Off-Topic - cold): human harsher on empathy
        {"test_run_id": 15, "human_score": 30.0, "human_failure_points": json.dumps([3, 5, 7]), "notes": "TODO: Replace with your own hand-score. Robotic and alienating."},
        # Run 16 (Competitor - effective): close agreement
        {"test_run_id": 16, "human_score": 93.0, "human_failure_points": json.dumps([]), "notes": "TODO: Replace with your own hand-score. Textbook competitive positioning."},
        # Run 17 (Competitor - generic): human harsher
        {"test_run_id": 17, "human_score": 55.0, "human_failure_points": json.dumps([3, 5]), "notes": "TODO: Replace with your own hand-score. Vague until pushed."},
        # Run 18 (Competitor - trash talk): strong agreement on failure
        {"test_run_id": 18, "human_score": 20.0, "human_failure_points": json.dumps([3, 5]), "notes": "TODO: Replace with your own hand-score. Unprofessional competitor bashing."},
    ]

    for cal in HUMAN_CALIBRATION:
        # Look up the judge score from the corresponding test run
        cursor.execute("SELECT overall_score FROM test_runs WHERE id = ?", (cal["test_run_id"],))
        row = cursor.fetchone()
        if row is None:
            logger.warning(f"Test run {cal['test_run_id']} not found, skipping calibration entry.")
            continue

        judge_score = row[0]
        cursor.execute(
            """INSERT INTO judge_calibration
               (test_run_id, human_score, human_failure_points, judge_score, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (
                cal["test_run_id"],
                cal["human_score"],
                cal["human_failure_points"],
                judge_score,
                cal["notes"],
            ),
        )

    conn.commit()
    conn.close()

    logger.info(
        f"Seeding complete: {len(SCENARIO_ROWS)} scenarios, "
        f"{len(SEED_TRANSCRIPTS)} test runs, "
        f"{len(HUMAN_CALIBRATION)} calibration entries."
    )


if __name__ == "__main__":
    seed_data()
