from db.db_base import db, log_activity, log_err
from enum import Enum as PyEnum
from sqlalchemy import ForeignKey, String, Integer, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.utils.utils import get_function

class ReviewStatusEnum(PyEnum):
    PendingConfirmation='Pending confirmation'
    RejectedByReviewer='Rejected by reviewer'
    AcceptedByReviewer='Accepted by reviewer'
    Reviewed='Reviewed'
    NotReviewed='Not reviewed'
    Expired='Expired'

class ReviewStatus(db.Model):
    __tablename__ = 'review_status'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stat: Mapped[ReviewStatusEnum] = mapped_column(Enum(ReviewStatusEnum), nullable=False, unique=True)

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    round_id: Mapped[int] = mapped_column(ForeignKey('rounds.id'), nullable=False)
    reviewer_id: Mapped[int] = mapped_column(ForeignKey('usr.id'), nullable=False)
    review_text: Mapped[str] = mapped_column(Text, nullable=True)
    status_id: Mapped[int] = mapped_column(ForeignKey('review_status.id'), nullable=False)
    
    round = relationship('Round', backref='reviews')
    reviewer = relationship('User', backref='reviews')
    status = relationship('ReviewStatus', backref='reviews')

    def update_status(self, new_status: ReviewStatusEnum) -> bool:
        try:
            status = ReviewStatus.query.where(ReviewStatus.stat == new_status).first()
            if status:
                self.status_id = status.id
                log_activity(get_function(), True, {'details': f'Changed review status with id: {self.id} to: {new_status.value}'})
                return True
            log_activity(get_function(), False, {'err': f'Review {self.id} status not changed to: {new_status.value} '})
            return False
        except Exception as e:
            db.session.rollback()
            log_err(get_function(), e)
            return False


'''
Pending confirmation - Oczekiwanie na potwierdzenie recenzenta, że podejmie się recenzowania.
Rejected by reviewer - Odrzucone przez recenzenta.
Accepted by reviewer - Zaakceptowane przez recenzenta, który zobowiązał się przygotować recenzję.
Reviewed - Recenzja została zakończona (dostarczona przez recenzenta).
Not reviewed - Brak recenzji, ponieważ recenzent nie zdążył przygotować jej na czas pomimo akceptacji.
Expired - Nie potwierdził w wyznaczonym terminie czy będize recenzować.
'''