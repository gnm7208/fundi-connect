"""Authentication and user management service."""

from flask_jwt_extended import create_access_token, create_refresh_token

from server.extensions import db
from server.models.category import Category
from server.models.fundi_profile import FundiProfile, FundiSkill
from server.models.user import User
from server.models.wallet import Wallet
from server.utils.errors import AuthenticationError, ConflictError, ForbiddenError, NotFoundError
from server.utils.formatters import normalize_phone_number


class AuthService:
    """Handles user registration, authentication, and token management."""

    @classmethod
    def register_user(cls, data: dict) -> tuple[User, str, str]:
        """Register a new customer or fundi account."""
        email = data["email"].strip().lower()
        normalized_phone = normalize_phone_number(data["phone"])

        # Check uniqueness
        if User.query.filter_by(email=email).first():
            raise ConflictError("An account with this email already exists")
        if User.query.filter_by(phone=normalized_phone).first():
            raise ConflictError("An account with this phone number already exists")

        role = data.get("role", "customer")
        user = User(
            email=email,
            phone=normalized_phone,
            role=role,
            full_name=data["full_name"].strip(),
        )
        user.set_password(data["password"])
        db.session.add(user)
        db.session.flush()

        # Initialize Wallet for user
        wallet = Wallet(user_id=user.id, balance_cents=0)
        db.session.add(wallet)

        # If registering as a Fundi, create initial profile
        if role == "fundi":
            profile = FundiProfile(
                user_id=user.id,
                business_name=data.get("business_name") or user.full_name,
                location_name=data.get("location_name"),
                hourly_rate_cents=data.get("hourly_rate_cents", 150000),  # default KES 1,500/hr
                verification_status="pending",
            )
            db.session.add(profile)
            db.session.flush()

            # Optional initial category/skill
            category_id = data.get("category_id")
            if category_id:
                category = db.session.get(Category, category_id)
                if category:
                    skill = FundiSkill(
                        fundi_profile_id=profile.id,
                        category_id=category.id,
                        skill_name=category.name,
                    )
                    db.session.add(skill)

        db.session.commit()

        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        return user, access_token, refresh_token

    @classmethod
    def authenticate_user(cls, email_or_phone: str, password: str) -> tuple[User, str, str]:
        """Authenticate user by email or phone and return tokens."""
        identifier = email_or_phone.strip()
        user = None

        if "@" in identifier:
            user = User.query.filter_by(email=identifier.lower()).first()
        else:
            try:
                phone = normalize_phone_number(identifier)
                user = User.query.filter_by(phone=phone).first()
            except Exception:
                user = User.query.filter_by(phone=identifier).first()

        if not user or not user.check_password(password):
            raise AuthenticationError("Invalid login credentials")

        if not user.is_active:
            raise AuthenticationError("Account has been deactivated. Please contact support.")

        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        return user, access_token, refresh_token

    @classmethod
    def get_user_profile(cls, user_id: str) -> User:
        """Fetch user profile with related data."""
        user = db.session.get(User, user_id)
        if not user:
            raise NotFoundError("User not found")
        return user

    # Bookings in any of these states still have work or money in flight.
    ACTIVE_BOOKING_STATUSES = (
        "pending",
        "accepted_unpaid",
        "escrow_funded",
        "in_progress",
        "awaiting_confirm",
        "disputed",
    )

    @classmethod
    def delete_account(cls, user: User, password: str) -> None:
        """Erase a user and everything only they own, once nothing is in flight.

        Refuses while the user has active bookings, money held in escrow or a
        wallet balance: a deletion must never strand a counterparty or funds.
        Dependent rows are removed explicitly rather than trusting ON DELETE
        CASCADE, because SQLite (dev/tests) does not enforce foreign keys and
        the ORM would otherwise try to NULL non-nullable columns.
        """
        from server.models.booking import Booking
        from server.models.conversation import Conversation, Message
        from server.models.escrow import EscrowTransaction
        from server.models.service_request import Quote, ServiceRequest

        if not password or not user.check_password(password):
            # 403, not 401: the session is fine, only the confirmation failed,
            # and the client signs the user out on any 401.
            raise ForbiddenError("Incorrect password")
        if user.is_admin():
            raise ForbiddenError("Administrator accounts are removed by another administrator")

        involved = (Booking.customer_id == user.id) | (Booking.fundi_id == user.id)
        active = (
            db.session.query(Booking)
            .filter(involved, Booking.status.in_(cls.ACTIVE_BOOKING_STATUSES))
            .count()
        )
        if active:
            raise ConflictError("Finish or cancel your active jobs before deleting your account")
        held = (
            db.session.query(EscrowTransaction)
            .filter(
                (EscrowTransaction.customer_id == user.id)
                | (EscrowTransaction.fundi_id == user.id),
                EscrowTransaction.status == "held_in_escrow",
            )
            .count()
        )
        if held:
            raise ConflictError("Money is still held in escrow on one of your jobs")
        if user.wallet and user.wallet.balance_cents > 0:
            raise ConflictError("Withdraw your wallet balance before deleting your account")

        # Conversations (and their messages) with anyone.
        for conversation in (
            db.session.query(Conversation)
            .filter((Conversation.customer_id == user.id) | (Conversation.fundi_id == user.id))
            .all()
        ):
            db.session.query(Message).filter(Message.conversation_id == conversation.id).delete(
                synchronize_session=False
            )
            db.session.delete(conversation)
        db.session.query(Message).filter(Message.sender_id == user.id).delete(
            synchronize_session=False
        )
        # Quotes they gave as a fundi, then requests they posted as a customer
        # (which take their own quotes with them).
        db.session.query(Quote).filter(Quote.fundi_id == user.id).delete(synchronize_session=False)
        for service_request in (
            db.session.query(ServiceRequest).filter(ServiceRequest.customer_id == user.id).all()
        ):
            db.session.delete(service_request)
        # Finished bookings on either side; escrow, review and dispute rows
        # cascade from the booking.
        for booking in db.session.query(Booking).filter(involved).all():
            db.session.delete(booking)
        db.session.flush()

        # Profile, skills, wallet, wallet history and notifications cascade
        # from the user via the ORM relationships.
        db.session.delete(user)
        db.session.commit()
