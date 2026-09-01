"""Authentication and user management service."""

from flask_jwt_extended import create_access_token, create_refresh_token

from server.extensions import db
from server.models.category import Category
from server.models.fundi_profile import FundiProfile, FundiSkill
from server.models.user import User
from server.models.wallet import Wallet
from server.utils.errors import AuthenticationError, ConflictError, NotFoundError
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
