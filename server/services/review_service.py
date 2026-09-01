"""Customer review and fundi rating calculation service."""

from server.extensions import db
from server.models.booking import Booking
from server.models.fundi_profile import FundiProfile
from server.models.review import Review
from server.models.user import User
from server.utils.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError


class ReviewService:
    """Manages verified client reviews and dynamic fundi ratings."""

    @classmethod
    def create_review(
        cls, customer: User, booking_id: str, rating: int, review_text: str | None
    ) -> Review:
        """Create a verified review for a completed job booking."""
        booking = db.session.get(Booking, booking_id)
        if not booking:
            raise NotFoundError("Booking not found")

        if booking.customer_id != customer.id and not customer.is_admin():
            raise ForbiddenError("Only the customer of this booking can leave a review")

        if booking.status != "completed":
            raise ValidationError("Reviews can only be submitted after a booking is completed")

        if booking.review:
            raise ConflictError("A review has already been submitted for this booking")

        fundi_profile = FundiProfile.query.filter_by(user_id=booking.fundi_id).first()
        if not fundi_profile:
            raise NotFoundError("Fundi profile not found")

        review = Review(
            booking_id=booking.id,
            customer_id=customer.id,
            fundi_id=fundi_profile.id,
            rating=rating,
            review_text=review_text,
        )
        db.session.add(review)

        # Recalculate fundi rating average
        current_count = fundi_profile.rating_count
        current_avg = fundi_profile.rating_avg
        new_count = current_count + 1
        new_avg = ((current_avg * current_count) + rating) / new_count

        fundi_profile.rating_avg = round(new_avg, 2)
        fundi_profile.rating_count = new_count

        db.session.commit()
        return review
