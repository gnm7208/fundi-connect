"""Seed database with realistic Kenyan informal-services marketplace data."""

import os
import sys
from datetime import UTC, datetime, timedelta

# Add workspace to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server.app import create_app
from server.extensions import db
from server.models.booking import Booking
from server.models.category import Category
from server.models.conversation import Conversation, Message
from server.models.escrow import EscrowTransaction
from server.models.fundi_profile import FundiProfile, FundiSkill
from server.models.review import Review
from server.models.service_request import Quote, ServiceRequest
from server.models.user import User
from server.models.wallet import Wallet, WalletTransaction
from server.services.escrow_service import EscrowService


def utc_now():
    return datetime.now(UTC)


def seed_database():
    app = create_app("development")

    with app.app_context():
        print("🌱 Seeding Fundi Connect database...")
        db.drop_all()
        db.create_all()

        # 1. Categories
        categories_data = [
            {
                "name": "Plumbing & Drainage",
                "slug": "plumbing",
                "description": "Pipe repair, unblocking sinks/toilets, leak detection, water tank installations.",
                "icon": "Wrench",
            },
            {
                "name": "Electrical & Wiring",
                "slug": "electrical",
                "description": "Lighting, socket repairs, circuit breakers, backup generators, solar wiring.",
                "icon": "Zap",
            },
            {
                "name": "Carpentry & Joinery",
                "slug": "carpentry",
                "description": "Custom furniture, cabinet repairs, door hanging, roof timber repair.",
                "icon": "Hammer",
            },
            {
                "name": "Mama Fua & Cleaning",
                "slug": "cleaning",
                "description": "Household laundry (Mama Fua), deep cleaning, post-construction cleanup.",
                "icon": "Sparkles",
            },
            {
                "name": "Appliance & Phone Repair",
                "slug": "appliance-repair",
                "description": "Washing machines, microwaves, TV repair, smartphone screen and battery fixes.",
                "icon": "Cpu",
            },
            {
                "name": "Masonry & Tiling",
                "slug": "masonry",
                "description": "Floor tiling, bricklaying, wall plastering, foundation repairs.",
                "icon": "Building",
            },
            {
                "name": "Painting & Gypsum",
                "slug": "painting",
                "description": "Interior/exterior wall painting, decorative finishes, gypsum ceilings.",
                "icon": "Paintbrush",
            },
            {
                "name": "Welding & Metal Fabrication",
                "slug": "welding",
                "description": "Window grills, steel gates, metal fabrication, security barriers.",
                "icon": "Flame",
            },
        ]

        categories_map = {}
        for c_data in categories_data:
            cat = Category(**c_data)
            db.session.add(cat)
            db.session.flush()
            categories_map[cat.slug] = cat

        # 2. Administrator
        admin = User(
            email="admin@fundiconnect.co.ke",
            phone="254700000001",
            role="admin",
            full_name="Fundi Connect Admin",
        )
        admin.set_password("fundi123")
        db.session.add(admin)
        db.session.flush()

        admin_wallet = Wallet(user_id=admin.id, balance_cents=0)
        db.session.add(admin_wallet)

        # 3. Customers
        customers_data = [
            {
                "email": "sarah.kimani@gmail.com",
                "phone": "254711111111",
                "full_name": "Sarah Kimani",
                "role": "customer",
            },
            {
                "email": "kevin.ochieng@gmail.com",
                "phone": "254722222222",
                "full_name": "Kevin Ochieng",
                "role": "customer",
            },
            {
                "email": "amina.abdi@gmail.com",
                "phone": "254733333333",
                "full_name": "Amina Abdi",
                "role": "customer",
            },
        ]

        customers = []
        for cust_data in customers_data:
            cust = User(**cust_data)
            cust.set_password("fundi123")
            db.session.add(cust)
            db.session.flush()
            w = Wallet(user_id=cust.id, balance_cents=0)
            db.session.add(w)
            customers.append(cust)

        sarah, kevin, amina = customers

        # 4. Verified Fundis across Nairobi
        fundis_seed = [
            {
                "user": {
                    "email": "john.mwangi@fundi.co.ke",
                    "phone": "254712345678",
                    "full_name": "John Mwangi",
                    "role": "fundi",
                },
                "profile": {
                    "business_name": "Mwangi Master Plumbers",
                    "bio": "Certified plumber with 9+ years experience solving Nairobi leaks, instant shower installations, and bathroom redesigns.",
                    "experience_years": 9,
                    "id_number": "28374912",
                    "id_document_url": "https://example.com/docs/mwangi_id.pdf",
                    "verification_status": "verified",
                    "verified_at": utc_now() - timedelta(days=90),
                    "location_name": "Kilimani, Nairobi",
                    "latitude": -1.2921,
                    "longitude": 36.7845,
                    "service_radius_km": 20.0,
                    "hourly_rate_cents": 180000,  # KES 1,800/hr
                    "rating_avg": 4.92,
                    "rating_count": 28,
                    "jobs_completed": 34,
                },
                "skills": ["plumbing"],
                "wallet_balance": 450000,  # KES 4,500
            },
            {
                "user": {
                    "email": "otieno.sparks@fundi.co.ke",
                    "phone": "254723456789",
                    "full_name": "Otieno James",
                    "role": "fundi",
                },
                "profile": {
                    "business_name": "Oti Electrical & Solar Solutions",
                    "bio": "EPRA Class B licensed electrician. Specializing in domestic wiring, solar inverters, and fault troubleshooting.",
                    "experience_years": 7,
                    "id_number": "31948201",
                    "id_document_url": "https://example.com/docs/otieno_epra.pdf",
                    "verification_status": "verified",
                    "verified_at": utc_now() - timedelta(days=60),
                    "location_name": "Westlands, Nairobi",
                    "latitude": -1.2683,
                    "longitude": 36.8111,
                    "service_radius_km": 25.0,
                    "hourly_rate_cents": 200000,  # KES 2,000/hr
                    "rating_avg": 4.88,
                    "rating_count": 32,
                    "jobs_completed": 41,
                },
                "skills": ["electrical"],
                "wallet_balance": 1200000,  # KES 12,000
            },
            {
                "user": {
                    "email": "grace.wanjiku@fundi.co.ke",
                    "phone": "254734567890",
                    "full_name": "Grace Wanjiku",
                    "role": "fundi",
                },
                "profile": {
                    "business_name": "Mama Grace Home Cleaners",
                    "bio": "Trusted household cleaning and laundry service (Mama Fua) with vetted team for residential apartments and offices.",
                    "experience_years": 5,
                    "id_number": "33829104",
                    "id_document_url": "https://example.com/docs/grace_id.pdf",
                    "verification_status": "verified",
                    "verified_at": utc_now() - timedelta(days=45),
                    "location_name": "Eastleigh & CBD, Nairobi",
                    "latitude": -1.2750,
                    "longitude": 36.8520,
                    "service_radius_km": 15.0,
                    "hourly_rate_cents": 120000,  # KES 1,200/hr
                    "rating_avg": 5.0,
                    "rating_count": 19,
                    "jobs_completed": 24,
                },
                "skills": ["cleaning"],
                "wallet_balance": 360000,  # KES 3,600
            },
            {
                "user": {
                    "email": "kamau.wood@fundi.co.ke",
                    "phone": "254745678901",
                    "full_name": "Peter Kamau",
                    "role": "fundi",
                },
                "profile": {
                    "business_name": "Ngong Road Custom Woodworks",
                    "bio": "Master carpenter crafting bespoke mahogany tables, wardrobing, and kitchen remodeling.",
                    "experience_years": 11,
                    "id_number": "26481923",
                    "id_document_url": "https://example.com/docs/kamau_cert.pdf",
                    "verification_status": "verified",
                    "verified_at": utc_now() - timedelta(days=120),
                    "location_name": "Ngong Road / Karen, Nairobi",
                    "latitude": -1.3005,
                    "longitude": 36.7550,
                    "service_radius_km": 30.0,
                    "hourly_rate_cents": 160000,  # KES 1,600/hr
                    "rating_avg": 4.75,
                    "rating_count": 16,
                    "jobs_completed": 20,
                },
                "skills": ["carpentry"],
                "wallet_balance": 800000,
            },
            {
                "user": {
                    "email": "hassan.phone@fundi.co.ke",
                    "phone": "254756789012",
                    "full_name": "Hassan Noor",
                    "role": "fundi",
                },
                "profile": {
                    "business_name": "QuickFix Gadgets & Phones",
                    "bio": "Expert repair of Apple, Samsung, Xiaomi devices, TV motherboards, and microwave circuits.",
                    "experience_years": 4,
                    "id_number": "35819204",
                    "id_document_url": "https://example.com/docs/hassan_id.pdf",
                    "verification_status": "verified",
                    "verified_at": utc_now() - timedelta(days=20),
                    "location_name": "Roysambu / Thika Road, Nairobi",
                    "latitude": -1.2185,
                    "longitude": 36.8875,
                    "service_radius_km": 15.0,
                    "hourly_rate_cents": 100000,  # KES 1,000/hr
                    "rating_avg": 4.82,
                    "rating_count": 11,
                    "jobs_completed": 15,
                },
                "skills": ["appliance-repair"],
                "wallet_balance": 250000,
            },
            {
                "user": {
                    "email": "brian.fixes@fundi.co.ke",
                    "phone": "254767890123",
                    "full_name": "Brian Kipkorir",
                    "role": "fundi",
                },
                "profile": {
                    "business_name": "South B Plumbing & Repairs",
                    "bio": "Young energetic technician specializing in residential plumbing and general handyman tasks.",
                    "experience_years": 2,
                    "id_number": "38491024",
                    "id_document_url": "https://example.com/docs/brian_id.pdf",
                    "verification_status": "pending",  # Pending verification
                    "location_name": "South B, Nairobi",
                    "latitude": -1.3120,
                    "longitude": 36.8340,
                    "service_radius_km": 10.0,
                    "hourly_rate_cents": 120000,
                    "rating_avg": 0.0,
                    "rating_count": 0,
                    "jobs_completed": 0,
                },
                "skills": ["plumbing"],
                "wallet_balance": 0,
            },
        ]

        created_fundis = []
        for f_data in fundis_seed:
            f_user = User(**f_data["user"])
            f_user.set_password("fundi123")
            db.session.add(f_user)
            db.session.flush()

            profile_data = dict(f_data["profile"])
            profile_data["user_id"] = f_user.id
            profile = FundiProfile(**profile_data)
            db.session.add(profile)
            db.session.flush()

            for skill_slug in f_data["skills"]:
                if skill_slug in categories_map:
                    skill = FundiSkill(
                        fundi_profile_id=profile.id,
                        category_id=categories_map[skill_slug].id,
                        skill_name=categories_map[skill_slug].name,
                        experience_years=profile.experience_years,
                    )
                    db.session.add(skill)

            wallet = Wallet(user_id=f_user.id, balance_cents=f_data["wallet_balance"])
            db.session.add(wallet)
            db.session.flush()

            if f_data["wallet_balance"] > 0:
                tx = WalletTransaction(
                    wallet_id=wallet.id,
                    type="escrow_payout",
                    amount_cents=f_data["wallet_balance"],
                    balance_after_cents=f_data["wallet_balance"],
                    status="completed",
                    description="Opening balance from completed escrow jobs",
                )
                db.session.add(tx)

            created_fundis.append((f_user, profile))

        john_user, john_prof = created_fundis[0]
        oti_user, oti_prof = created_fundis[1]
        grace_user, grace_prof = created_fundis[2]
        kamau_user, kamau_prof = created_fundis[3]

        # 5. Service Requests & Quotes
        sr1 = ServiceRequest(
            customer_id=sarah.id,
            category_id=categories_map["plumbing"].id,
            title="Leaking Kitchen Sink & Low Water Pressure",
            description="The pipe under my kitchen sink has a steady leak damaging the wooden cabinet, and hot water pressure in the master bathroom is very low.",
            location_name="Kilimani, Wood Avenue",
            latitude=-1.2930,
            longitude=36.7860,
            budget_min_cents=200000,
            budget_max_cents=350000,
            preferred_date=utc_now() + timedelta(days=1),
            status="open",
        )
        db.session.add(sr1)
        db.session.flush()

        # Quotes for SR1
        q1 = Quote(
            service_request_id=sr1.id,
            fundi_id=john_user.id,
            amount_cents=250000,  # KES 2,500
            estimated_hours=2.5,
            notes="I am in Kilimani and can bring replacement copper fittings and high pressure pressure valve.",
            status="pending",
        )
        db.session.add(q1)

        # 6. Completed Booking with Escrow Release & Review
        b1_agreed = 350000  # KES 3,500
        p_fee, f_payout = EscrowService.calculate_breakdown(b1_agreed)
        b1 = Booking(
            customer_id=kevin.id,
            fundi_id=oti_user.id,
            title="Rewiring Living Room & Installing Chandelier",
            description="Replace old wiring switches and install heavy crystal chandelier with double switches.",
            agreed_amount_cents=b1_agreed,
            platform_fee_cents=p_fee,
            fundi_amount_cents=f_payout,
            location_name="Westlands, Rhapta Road",
            latitude=-1.2670,
            longitude=36.8090,
            status="completed",
            scheduled_for=utc_now() - timedelta(days=5),
            started_at=utc_now() - timedelta(days=5, hours=2),
            completed_at=utc_now() - timedelta(days=5),
        )
        db.session.add(b1)
        db.session.flush()

        escrow1 = EscrowTransaction(
            booking_id=b1.id,
            customer_id=kevin.id,
            fundi_id=oti_user.id,
            amount_cents=b1_agreed,
            platform_fee_cents=p_fee,
            fundi_payout_cents=f_payout,
            status="released",
            mpesa_receipt_number="QWE9873210",
            payment_phone=kevin.phone,
            funded_at=utc_now() - timedelta(days=5, hours=3),
            released_at=utc_now() - timedelta(days=5),
        )
        db.session.add(escrow1)

        r1 = Review(
            booking_id=b1.id,
            customer_id=kevin.id,
            fundi_id=oti_prof.id,
            rating=5,
            review_text="Otieno did a fantastic job installing our chandelier! Very clean work, arrived exactly on time, and tested all circuits. Highly recommend.",
            created_at=utc_now() - timedelta(days=5),
        )
        db.session.add(r1)

        # 7. Active Escrow Job (Currently In Progress)
        b2_agreed = 240000  # KES 2,400
        p_fee2, f_payout2 = EscrowService.calculate_breakdown(b2_agreed)
        b2 = Booking(
            customer_id=amina.id,
            fundi_id=grace_user.id,
            title="Mama Fua: Full House Deep Clean & Laundry",
            description="Deep cleaning of 3-bedroom apartment and washing bed linens.",
            agreed_amount_cents=b2_agreed,
            platform_fee_cents=p_fee2,
            fundi_amount_cents=f_payout2,
            location_name="Eastleigh 2nd Avenue",
            latitude=-1.2740,
            longitude=36.8510,
            status="in_progress",
            scheduled_for=utc_now(),
            started_at=utc_now() - timedelta(hours=1),
        )
        db.session.add(b2)
        db.session.flush()

        escrow2 = EscrowTransaction(
            booking_id=b2.id,
            customer_id=amina.id,
            fundi_id=grace_user.id,
            amount_cents=b2_agreed,
            platform_fee_cents=p_fee2,
            fundi_payout_cents=f_payout2,
            status="held_in_escrow",
            checkout_request_id="ws_CO_DEMO_ESCROW_12345",
            mpesa_receipt_number="QAA1122334",
            payment_phone=amina.phone,
            funded_at=utc_now() - timedelta(hours=2),
        )
        db.session.add(escrow2)

        # 8. Sample Conversation
        conv = Conversation(
            customer_id=sarah.id,
            fundi_id=john_user.id,
            booking_id=None,
            last_message_at=utc_now(),
        )
        db.session.add(conv)
        db.session.flush()

        m1 = Message(
            conversation_id=conv.id,
            sender_id=sarah.id,
            content="Habari John, are you available tomorrow morning around 9am for the plumbing job?",
            created_at=utc_now() - timedelta(minutes=30),
        )
        m2 = Message(
            conversation_id=conv.id,
            sender_id=john_user.id,
            content="Habari Sarah! Yes, 9:00 AM works perfectly. I will come with the required pipe fittings and Teflon tape.",
            created_at=utc_now() - timedelta(minutes=15),
        )
        db.session.add_all([m1, m2])

        db.session.commit()
        print("✅ Database seeding complete!")
        print(f"   Admin: {admin.email} / fundi123")
        print(f"   Customer: {sarah.email} / fundi123")
        print(f"   Fundi (Plumber): {john_user.email} / fundi123")
        print(f"   Fundi (Electrician): {oti_user.email} / fundi123")


if __name__ == "__main__":
    seed_database()
