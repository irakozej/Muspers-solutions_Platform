"""Populate the database with 8 realistic Rwandan SME clients + full diagnostic
sessions, chat transcripts, reports, ratings, and notes.

Idempotent: every demo user (email ending in '@demo.musper.com') and all their
related data is wiped before reseeding, so re-running gives the exact same state.

Usage:
    cd backend
    uv run python -m scripts.seed_mock_data
"""
from __future__ import annotations

import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Make sys.path include the backend dir.
HERE = Path(__file__).resolve()
BACKEND_DIR = HERE.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import delete, select  # noqa: E402

from app.core.scoring import band_for, finance_readiness, grow_overall  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.advisor_note import AdvisorNote  # noqa: E402
from app.models.chat_message import ChatMessage, MessageRole  # noqa: E402
from app.models.client import BusinessSize, Client  # noqa: E402
from app.models.diagnostic_session import DiagnosticSession, SessionStatus  # noqa: E402
from app.models.rating import Rating  # noqa: E402
from app.models.report import Report  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402


DEMO_EMAIL_DOMAIN = "@demo.musper.com"
DEMO_PASSWORD = "DemoClient1!"


def _utc(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, 14, 30, tzinfo=timezone.utc)


# ───────────────────── chat template ─────────────────────

QUESTIONS = [
    "Welcome to your MusperSolutions diagnostic. To start, give me your business in two sentences.",
    "Walk me through how you bring in revenue today, what are the main streams?",
    "Where do new customers come from for you right now?",
    "When something goes wrong in delivery or production, how do you find out?",
    "Do you have a clear view of cash flow over the next 90 days?",
    "Tell me about your team, what does the org look like, top to bottom?",
    "What's the single biggest constraint on your growth right now?",
]
CLOSING = (
    "Thank you. I have a clear picture. I'll synthesise the priority actions "
    "and we'll send the report through within the week."
)


def build_transcript(*, answers: list[str], started_at: datetime) -> list[dict]:
    """Returns alternating assistant/user messages, paced ~3 minutes between turns."""
    if len(answers) != len(QUESTIONS):
        raise ValueError("answers must match QUESTIONS in length")
    msgs: list[dict] = []
    t = started_at
    for q, a in zip(QUESTIONS, answers):
        msgs.append({"role": MessageRole.assistant, "content": q, "at": t})
        t += timedelta(minutes=2, seconds=30)
        msgs.append({"role": MessageRole.user, "content": a, "at": t})
        t += timedelta(minutes=3)
    msgs.append({"role": MessageRole.assistant, "content": CLOSING, "at": t})
    return msgs


# ───────────────────── client profiles ─────────────────────

CLIENTS = [
    {
        "slug": "client01",
        "full_name": "Marie-Claire Uwase",
        "business_name": "Inyange Foods Ltd",
        "sector": "Agro-processing",
        "location": "Kicukiro, Kigali",
        "business_size": BusinessSize.medium,
        "employee_count": 45,
        "founded_year": 2014,
        "revenue_band": "200M-500M RWF",
        "revenue_trend": [
            {"period": "Q1 '24", "revenue_mrwf": 150},
            {"period": "Q2 '24", "revenue_mrwf": 165},
            {"period": "Q3 '24", "revenue_mrwf": 175},
            {"period": "Q4 '24", "revenue_mrwf": 185},
            {"period": "Q1 '25", "revenue_mrwf": 195},
            {"period": "Q2 '25", "revenue_mrwf": 210},
        ],
        "answers": [
            "We process fruit and vegetable products, pineapple juice, tomato paste, dried mango, sold in Kigali supermarkets and to two regional distributors.",
            "Three streams: supermarket distribution in Rwanda (about 60%), wholesale to Uganda and Burundi distributors (30%), and an institutional contract with a school feeding program (10%).",
            "Mostly the buyers come to us, we have multi-year contracts with the supermarkets. New growth is via the school program and Uganda referrals.",
            "Our production manager flags it on the floor, and we have a daily morning huddle. Bigger quality issues come back through the supermarkets within a week.",
            "Yes, we have a monthly cash flow but it's mostly historical. Forward visibility is maybe 30 days.",
            "I'm the CEO, my brother handles operations, we have a finance lead, a production manager, a sales lead, and 40 production staff. The production team has a lot of turnover.",
            "Talent. We're losing skilled production line workers every 6-9 months and it's slowing our quality consistency.",
        ],
        "scores": {"strategy": 72, "customers": 68, "money": 75, "operations": 82, "talent": 55},
        "summary": (
            "Inyange runs a disciplined operation with strong delivery and stable contracts. The "
            "binding constraint is talent retention on the production floor, which is now starting "
            "to show up as quality variability. Money and operations are solid; talent needs work."
        ),
        "red_flags": [
            "High staff turnover in production line (>40% annual)",
            "Limited succession planning at management level",
        ],
        "priority_actions": [
            {
                "title": "Build a tiered retention plan for production staff",
                "detail": "Define skill bands + a 6/12/18-month retention bonus aligned to certification milestones.",
                "owner": "HR + Operations Manager",
                "horizon": "30 days",
            },
            {
                "title": "Document SOPs for top 3 product lines",
                "detail": "Capture pineapple juice, tomato paste, and mango drying procedures in writing so quality survives turnover.",
                "owner": "Production Manager",
                "horizon": "60 days",
            },
        ],
        "suggested_topics": [
            "Performance management for production teams",
            "Talent retention strategies for SMEs",
            "Succession planning for founder-led businesses",
        ],
        "is_shared": True,
        "rating": (5, "Very practical and tailored to our context. The retention plan is already in motion."),
        "session_completed_days_ago": 8,
        "advisor_notes": [
            "Marie-Claire is open to a follow-up clinic on retention, schedule for Q3.",
            "Brother (Ops Manager) likely needs leadership coaching before succession can move.",
        ],
    },
    {
        "slug": "client02",
        "full_name": "Jean-Baptiste Habyarimana",
        "business_name": "Karame Coffee Co.",
        "sector": "Coffee export",
        "location": "Huye, Southern Province",
        "business_size": BusinessSize.small,
        "employee_count": 18,
        "founded_year": 2017,
        "revenue_band": "50M-200M RWF",
        "revenue_trend": [
            {"period": "Q1 '24", "revenue_mrwf": 60},
            {"period": "Q2 '24", "revenue_mrwf": 50},
            {"period": "Q3 '24", "revenue_mrwf": 90},
            {"period": "Q4 '24", "revenue_mrwf": 110},
            {"period": "Q1 '25", "revenue_mrwf": 80},
            {"period": "Q2 '25", "revenue_mrwf": 95},
        ],
        "answers": [
            "Karame is a specialty coffee exporter, we source from 200+ smallholder farmers around Huye, mill, and export green beans, mostly to European roasters.",
            "Pretty much all export sales to European specialty roasters. About 80% to three German roasters and 20% to a UK partner.",
            "Mostly trade shows and roaster referrals. One of our German buyers has introduced us to three new roasters this year.",
            "Quality complaints come from buyers via email, usually 4-6 weeks after shipment. By then we can't trace it back to a specific lot easily.",
            "Honestly no, our money is locked up in the harvest cycle. Between buying cherries and getting paid by exporters, we go 4-5 months out of pocket.",
            "Me, my co-founder (head of sourcing), a milling supervisor, an export logistics person, two field officers, and the rest are mill workers seasonal.",
            "Working capital. I cannot say yes to bigger contracts because I can't fund the cherry purchase up front.",
        ],
        "scores": {"strategy": 64, "customers": 78, "money": 48, "operations": 60, "talent": 70},
        "summary": (
            "Karame has a strong customer position and respected product, but the business is "
            "starved of working capital and lacks systems to manage FX and pricing exposure. "
            "Without these fixes, growth opportunities will keep getting turned down."
        ),
        "red_flags": [
            "Cash flow gaps between cherry purchase and export payment (4-5 months)",
            "No formal pricing model, margins eroded by FX volatility",
        ],
        "priority_actions": [
            {
                "title": "Implement a rolling 13-week cash flow forecast",
                "detail": "Build a simple weekly cash projection covering cherry buying, milling, shipment, and receivables.",
                "owner": "Co-founder + Bookkeeper",
                "horizon": "21 days",
            },
            {
                "title": "Build a documented pricing model that prices in FX risk",
                "detail": "Move from gut-feel pricing to a model that locks in margin assuming +/- 8% FX swing.",
                "owner": "CEO",
                "horizon": "45 days",
            },
        ],
        "suggested_topics": [
            "SME working-capital strategies for exporters",
            "FX risk management basics",
            "Investment-readiness for the export sector",
        ],
        "is_shared": True,
        "rating": (4, "Useful framing. The 13-week forecast is doable; we'd appreciate help on the FX piece."),
        "session_completed_days_ago": 14,
        "advisor_notes": [
            "Introduce JB to the SIYB cohort facilitator who works with coffee exporters.",
        ],
    },
    {
        "slug": "client03",
        "full_name": "Rosine Mukamana",
        "business_name": "Heza Hospitality Group",
        "sector": "Hospitality & Tourism",
        "location": "Musanze, Northern Province",
        "business_size": BusinessSize.medium,
        "employee_count": 68,
        "founded_year": 2011,
        "revenue_band": "200M-500M RWF",
        "revenue_trend": [
            {"period": "Q1 '24", "revenue_mrwf": 120},
            {"period": "Q2 '24", "revenue_mrwf": 145},
            {"period": "Q3 '24", "revenue_mrwf": 180},
            {"period": "Q4 '24", "revenue_mrwf": 220},
            {"period": "Q1 '25", "revenue_mrwf": 245},
            {"period": "Q2 '25", "revenue_mrwf": 260},
        ],
        "answers": [
            "We run two boutique lodges and a tour-operating arm focused on gorilla trekking and cultural tourism in the Volcanoes region.",
            "Three streams: lodge stays (55%), tour packages (35%), and a small spa/wellness operation (10%).",
            "About 65% of revenue comes through one large international tour operator. The rest is direct online and partner travel agencies.",
            "Lodge managers report daily. Tour incidents come through guides via WhatsApp the same day. We're proud of our incident response.",
            "Yes, we run a monthly cash flow and a 90-day projection. The CFO updates it weekly.",
            "I'm CEO, we have a CFO, an Operations Director, two lodge managers, a tours lead, marketing lead, and ~60 staff across both lodges.",
            "Channel concentration. If our main tour operator drops us, we lose 65% overnight. It keeps me up.",
        ],
        "scores": {"strategy": 80, "customers": 85, "money": 72, "operations": 78, "talent": 76},
        "summary": (
            "Heza is a well-run operation with strong delivery and financial discipline. The "
            "principal risk is concentration: a single intermediary controls two-thirds of revenue. "
            "Diversifying channels is the highest-leverage move."
        ),
        "red_flags": [
            "Revenue concentration, 65% from a single tour operator",
        ],
        "priority_actions": [
            {
                "title": "Diversify channels, build direct online booking funnel",
                "detail": "Aim to move from 12% direct to 30% direct over 12 months. Hire a digital marketing lead.",
                "owner": "CEO + Marketing Lead",
                "horizon": "12 months",
            },
            {
                "title": "Pilot corporate retreats segment in Q3",
                "detail": "Test two corporate packages with Kigali-based companies and measure conversion.",
                "owner": "Tours Lead",
                "horizon": "90 days",
            },
        ],
        "suggested_topics": [
            "Channel diversification for hospitality",
            "Direct distribution strategies",
            "Pricing for premium segments",
        ],
        "is_shared": False,
        "rating": None,
        "session_completed_days_ago": 4,
        "advisor_notes": [],
    },
    {
        "slug": "client04",
        "full_name": "Aline Niyonsaba",
        "business_name": "Kigali Threads",
        "sector": "Fashion & Apparel",
        "location": "Nyarugenge, Kigali",
        "business_size": BusinessSize.small,
        "employee_count": 12,
        "founded_year": 2019,
        "revenue_band": "20M-50M RWF",
        "revenue_trend": [
            {"period": "Q1 '24", "revenue_mrwf": 25},
            {"period": "Q2 '24", "revenue_mrwf": 30},
            {"period": "Q3 '24", "revenue_mrwf": 32},
            {"period": "Q4 '24", "revenue_mrwf": 38},
            {"period": "Q1 '25", "revenue_mrwf": 42},
            {"period": "Q2 '25", "revenue_mrwf": 48},
        ],
        "answers": [
            "We design and produce contemporary African-print ready-to-wear, sold through one Kigali boutique we own and a small Instagram shop.",
            "About 70% physical retail at our shop, 30% Instagram + WhatsApp orders.",
            "Mostly Instagram. We get a lot of saves but conversion is slow. Walk-ins to the shop convert best.",
            "Honestly, often through customer complaints, sizing issues, late delivery on custom orders.",
            "Not really. We know what's in the bank but I don't have a 90-day view.",
            "I'm the designer/CEO, my sister is operations, we have 4 tailors, 2 cutters, 2 shop staff, a social media person, and a part-time accountant.",
            "Honestly, cash. We have orders we cannot deliver because we cannot pay for fabric up front.",
        ],
        "scores": {"strategy": 75, "customers": 70, "money": 45, "operations": 52, "talent": 65},
        "summary": (
            "Strong creative vision and growing demand, but the business is stretched thin "
            "operationally. Cost tracking is absent, inventory is heavy, and cash conversion is "
            "slow. Fixing the financial visibility is what makes the next stage possible."
        ),
        "red_flags": [
            "No unit-level cost tracking, gross margin is unknown",
            "Inventory carrying ~9 months, significant working capital lock-up",
        ],
        "priority_actions": [
            {
                "title": "Implement unit-level COGS tracking by month",
                "detail": "Capture fabric, labor, and overhead per garment style. Start with the top 5 SKUs.",
                "owner": "CEO + Accountant",
                "horizon": "30 days",
            },
            {
                "title": "Move to make-to-order for capsule lines",
                "detail": "Reduce upfront inventory by pre-selling capsule drops via Instagram with 50% deposit.",
                "owner": "CEO",
                "horizon": "60 days",
            },
        ],
        "suggested_topics": [
            "Costing & pricing for fashion SMEs",
            "Inventory management",
            "Make-to-order business models",
        ],
        "is_shared": False,
        "rating": None,
        "session_completed_days_ago": 11,
        "advisor_notes": [
            "Excellent candidate for the Women in Digital Business program.",
        ],
    },
    {
        "slug": "client05",
        "full_name": "Solange Iradukunda",
        "business_name": "Umurage Crafts",
        "sector": "Handicrafts & Retail",
        "location": "Nyamirambo, Kigali",
        "business_size": BusinessSize.micro,
        "employee_count": 6,
        "founded_year": 2020,
        "revenue_band": "<20M RWF",
        "revenue_trend": [
            {"period": "Q1 '24", "revenue_mrwf": 12},
            {"period": "Q2 '24", "revenue_mrwf": 11},
            {"period": "Q3 '24", "revenue_mrwf": 14},
            {"period": "Q4 '24", "revenue_mrwf": 13},
            {"period": "Q1 '25", "revenue_mrwf": 15},
            {"period": "Q2 '25", "revenue_mrwf": 16},
        ],
        "answers": [
            "We make handwoven baskets and small home decor pieces, sold mainly to tourists and one Kigali souvenir shop.",
            "Half from the souvenir shop, half from tourists who find us through guides.",
            "Word of mouth and guides. We're not really doing any marketing.",
            "I'm there every day so I see things directly.",
            "No, I don't track money in any structured way. I know roughly what's in the box.",
            "Me and five weavers, four women, one apprentice.",
            "Honestly I don't even know my margins. I price by what feels right at the time.",
        ],
        "scores": {"strategy": 55, "customers": 72, "money": 38, "operations": 50, "talent": 60},
        "summary": (
            "A loved product with a real customer base but no financial infrastructure. The "
            "personal-vs-business finance line doesn't exist yet. Foundation work first; growth "
            "tactics later."
        ),
        "red_flags": [
            "No separation of personal and business finances",
            "No formal bookkeeping for the last 6 months",
        ],
        "priority_actions": [
            {
                "title": "Open a dedicated business bank account this month",
                "detail": "Move all business income and expenses through it. Personal money stays personal.",
                "owner": "Founder",
                "horizon": "14 days",
            },
            {
                "title": "Adopt a simple monthly bookkeeping cadence",
                "detail": "Capture cash in / cash out on a single page each month. Just two columns to start.",
                "owner": "Founder",
                "horizon": "30 days",
            },
        ],
        "suggested_topics": [
            "Personal vs business finance separation",
            "Bookkeeping basics for micro-businesses",
            "Pricing handicraft products fairly",
        ],
        "is_shared": True,
        "rating": (5, "They made it feel doable. We've already opened the bank account."),
        "session_completed_days_ago": 22,
        "advisor_notes": [
            "Refer Solange to the next SIYB cohort, perfect fit.",
            "Follow up in 30 days to make sure the cash-in/cash-out sheet is being kept.",
        ],
    },
    {
        "slug": "client06",
        "full_name": "Patrick Mugabo",
        "business_name": "Asante Mobile Money Agents",
        "sector": "Financial services",
        "location": "Kigali",
        "business_size": BusinessSize.small,
        "employee_count": 22,
        "founded_year": 2018,
        "revenue_band": "50M-200M RWF",
        "revenue_trend": [
            {"period": "Q1 '24", "revenue_mrwf": 60},
            {"period": "Q2 '24", "revenue_mrwf": 75},
            {"period": "Q3 '24", "revenue_mrwf": 90},
            {"period": "Q4 '24", "revenue_mrwf": 110},
            {"period": "Q1 '25", "revenue_mrwf": 130},
            {"period": "Q2 '25", "revenue_mrwf": 155},
        ],
        "answers": [
            "We operate a network of 35 mobile money agent points across Kigali and Nyabugogo. We do deposits, withdrawals, bill payments.",
            "Commission on transactions through our partner telco, plus a small mark-up on certain bill-payment categories.",
            "Foot traffic at our agent points. We don't really 'acquire' customers, they walk up.",
            "Our area supervisors do daily route checks. Cash float issues get flagged via WhatsApp.",
            "Float management is our cash flow, basically. We're disciplined on that.",
            "I'm CEO, my partner handles operations, three area supervisors, and 18 agents at the points.",
            "Strategy. We've grown well but I haven't sat down to think about where we want to be in three years.",
        ],
        "scores": {"strategy": 50, "customers": 65, "money": 68, "operations": 76, "talent": 60},
        "summary": (
            "Operationally tight and growing, but strategy is reactive. The single-partner "
            "concentration is invisible until it isn't. A short strategic offsite would change the "
            "trajectory."
        ),
        "red_flags": [
            "No documented 3-year strategy",
            "Customer acquisition concentrated in one telco partnership",
        ],
        "priority_actions": [
            {
                "title": "Run a 1-day strategy session with leadership",
                "detail": "Set 3-year goals across volume, geography, and product mix. Document the plan in writing.",
                "owner": "CEO + Partner",
                "horizon": "45 days",
            },
            {
                "title": "Diversify partnerships across at least 2 telcos",
                "detail": "Negotiate with the second telco to onboard agent capacity within 6 months.",
                "owner": "CEO",
                "horizon": "6 months",
            },
        ],
        "suggested_topics": [
            "Strategic planning for SMEs",
            "Partnership risk management",
        ],
        "is_shared": False,
        "rating": None,
        "session_completed_days_ago": 18,
        "advisor_notes": [],
    },
    {
        "slug": "client07",
        "full_name": "Eric Bizimana",
        "business_name": "Imbuga Light Manufacturing",
        "sector": "Manufacturing",
        "location": "Special Economic Zone, Kigali",
        "business_size": BusinessSize.medium,
        "employee_count": 52,
        "founded_year": 2015,
        "revenue_band": "200M-500M RWF",
        "revenue_trend": [
            {"period": "Q1 '24", "revenue_mrwf": 180},
            {"period": "Q2 '24", "revenue_mrwf": 175},
            {"period": "Q3 '24", "revenue_mrwf": 185},
            {"period": "Q4 '24", "revenue_mrwf": 195},
            {"period": "Q1 '25", "revenue_mrwf": 190},
            {"period": "Q2 '25", "revenue_mrwf": 200},
        ],
        # In-progress session, no answers needed past the first few.
        "answers": None,
        "scores": None,  # No report yet
        "summary": None,
        "is_shared": False,
        "rating": None,
        "session_completed_days_ago": None,
        "in_progress": True,
        "in_progress_turns": 4,
        "in_progress_answers": [
            "We manufacture plastic household goods, buckets, basins, jerry cans, basic kitchenware, for the East African market.",
            "Mostly wholesale to distributors in Rwanda, Uganda, and Burundi. About 75/25 split between Rwanda and exports.",
        ],
        "advisor_notes": [
            "MusperSolutions started the session yesterday; Eric requested a pause to gather financials before the deep dive.",
        ],
    },
    {
        "slug": "client08",
        "full_name": "Diane Kanyana",
        "business_name": "Gisenyi Logistics",
        "sector": "Logistics & Transport",
        "location": "Rubavu, Western Province",
        "business_size": BusinessSize.small,
        "employee_count": 15,
        "founded_year": 2016,
        "revenue_band": "50M-200M RWF",
        "revenue_trend": [
            {"period": "Q1 '24", "revenue_mrwf": 80},
            {"period": "Q2 '24", "revenue_mrwf": 60},
            {"period": "Q3 '24", "revenue_mrwf": 55},
            {"period": "Q4 '24", "revenue_mrwf": 75},
            {"period": "Q1 '25", "revenue_mrwf": 95},
            {"period": "Q2 '25", "revenue_mrwf": 110},
        ],
        "answers": [
            "We run a small trucking fleet, 8 trucks, moving cargo between Goma, Rubavu, and Kigali. Mostly food and consumer goods.",
            "Per-trip charges to a small set of repeat clients, wholesalers and a couple of NGOs.",
            "Cold outreach by my partner, he visits warehouses in Kigali every two months.",
            "Drivers report in by phone. Cargo damage we usually find out at delivery.",
            "I have a rough monthly picture, not weekly or 90-day.",
            "Me, my partner, 8 drivers, a workshop mechanic, a dispatcher, and 4 part-time loaders.",
            "Drivers. We've lost 6 in the last 12 months and training new ones costs us in claims and downtime.",
        ],
        "scores": {"strategy": 60, "customers": 62, "money": 70, "operations": 65, "talent": 48},
        "summary": (
            "Cash discipline is reasonable but the workforce is fragile. Driver turnover is the "
            "operational weak point, every churned driver costs roughly two months of "
            "productivity to replace. Stabilising the team is the lever."
        ),
        "red_flags": [
            "Driver retention rate below 60% annually",
            "No formal safety training program",
        ],
        "priority_actions": [
            {
                "title": "Implement quarterly driver performance reviews",
                "detail": "Pair with a small retention bonus tied to clean-claims quarters. Cheap to run.",
                "owner": "Partner + Dispatcher",
                "horizon": "60 days",
            },
            {
                "title": "Roll out mandatory safety training for all drivers",
                "detail": "Half-day training quarterly, refreshers monthly. Reduces both claims and turnover.",
                "owner": "Partner",
                "horizon": "45 days",
            },
        ],
        "suggested_topics": [
            "Driver retention strategies for fleet SMEs",
            "Safety culture and risk reduction",
        ],
        "is_shared": False,
        "rating": (5, "Practical and free of jargon. The retention plan starts next quarter."),
        "session_completed_days_ago": 27,
        "advisor_notes": [],
    },
]


# ───────────────────── main ─────────────────────

def main() -> int:
    with SessionLocal() as db:
        # Wipe demo users (cascades to clients, sessions, messages, reports, ratings).
        demo_users = db.scalars(
            select(User).where(User.email.like(f"%{DEMO_EMAIL_DOMAIN}"))
        ).all()
        for u in demo_users:
            db.delete(u)
        db.commit()
        if demo_users:
            print(f"  cleared {len(demo_users)} previous demo users")

        # Find MusperSolutions (advisor), required for notes.
        advisor = db.scalar(select(User).where(User.role == UserRole.advisor))
        if advisor is None:
            print("✗  No advisor user found. Run `python -m scripts.seed_advisor` first.")
            return 1

        now = datetime.now(timezone.utc)

        for c in CLIENTS:
            email = f"{c['slug']}{DEMO_EMAIL_DOMAIN}"
            user = User(
                email=email,
                hashed_password=hash_password(DEMO_PASSWORD),
                role=UserRole.client,
                full_name=c["full_name"],
                is_verified=True,
            )
            db.add(user)
            db.flush()

            client = Client(
                user_id=user.id,
                business_name=c["business_name"],
                sector=c["sector"],
                location=c["location"],
                business_size=c["business_size"],
                employee_count=c["employee_count"],
                founded_year=c["founded_year"],
                revenue_band=c["revenue_band"],
                revenue_trend=c["revenue_trend"],
            )
            db.add(client)
            db.flush()

            if c.get("in_progress"):
                started = now - timedelta(days=1)
                session = DiagnosticSession(
                    client_id=client.id,
                    status=SessionStatus.in_progress,
                    started_at=started,
                )
                db.add(session)
                db.flush()
                # Partial transcript, just opening Q&A turns.
                t = started
                for i in range(c["in_progress_turns"] // 2):
                    db.add(
                        ChatMessage(
                            session_id=session.id,
                            role=MessageRole.assistant,
                            content=QUESTIONS[i],
                            created_at=t,
                        )
                    )
                    t += timedelta(minutes=2, seconds=30)
                    db.add(
                        ChatMessage(
                            session_id=session.id,
                            role=MessageRole.user,
                            content=c["in_progress_answers"][i],
                            created_at=t,
                        )
                    )
                    t += timedelta(minutes=3)
            else:
                completed_days_ago = c["session_completed_days_ago"]
                started = now - timedelta(days=completed_days_ago, minutes=30)
                completed = now - timedelta(days=completed_days_ago)
                session = DiagnosticSession(
                    client_id=client.id,
                    status=SessionStatus.completed,
                    started_at=started,
                    completed_at=completed,
                )
                db.add(session)
                db.flush()

                # Transcript
                for m in build_transcript(answers=c["answers"], started_at=started):
                    db.add(
                        ChatMessage(
                            session_id=session.id,
                            role=m["role"],
                            content=m["content"],
                            created_at=m["at"],
                        )
                    )

                # Report
                scores = dict(c["scores"])
                scores["grow_overall"] = grow_overall(scores)
                scores["grow_band"] = band_for(scores["grow_overall"])
                scores["finance_readiness"] = finance_readiness(scores)
                scores["finance_band"] = band_for(scores["finance_readiness"])

                report = Report(
                    session_id=session.id,
                    scores_json=scores,
                    content_json={
                        "summary": c["summary"],
                        "red_flags": c["red_flags"],
                        "priority_actions": c["priority_actions"],
                        "suggested_topics": c["suggested_topics"],
                    },
                    is_shared=c["is_shared"],
                    created_at=completed + timedelta(hours=2),
                )
                db.add(report)

                # Rating
                if c.get("rating"):
                    score, feedback = c["rating"]
                    db.add(
                        Rating(
                            session_id=session.id,
                            score=score,
                            feedback=feedback,
                            created_at=completed + timedelta(days=1),
                        )
                    )

            # Advisor notes (MusperSolutions' private notes)
            for i, note in enumerate(c.get("advisor_notes", [])):
                db.add(
                    AdvisorNote(
                        client_id=client.id,
                        advisor_id=advisor.id,
                        content=note,
                        created_at=now - timedelta(days=2, hours=i),
                    )
                )

            print(f"  ✓ {c['business_name']:35} ({email}), {DEMO_PASSWORD}")

        db.commit()

        print()
        print(f"✓ Seeded {len(CLIENTS)} demo clients.")
        print(f"  Every client password: {DEMO_PASSWORD}")
        print(f"  Sign in as any with: client01{DEMO_EMAIL_DOMAIN} ... client08{DEMO_EMAIL_DOMAIN}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
