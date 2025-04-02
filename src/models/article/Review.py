from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .Round import Round
from ..usr.User import User
from ...db.db_base import db
from sqlalchemy import ForeignKey, String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Review(db.Model):
    __tablename__ = 'reviews'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    round_id: Mapped[int] = mapped_column(ForeignKey('rounds.id'), nullable=False)
    reviewer_id: Mapped[int] = mapped_column(ForeignKey(User.id), nullable=False)
    review_text: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)

    round: Mapped["Round"] = relationship(back_populates='reviews')
    reviewer: Mapped[User] = relationship(foreign_keys=[reviewer_id])


'''
Pending confirmation - Oczekiwanie na potwierdzenie recenzenta, że podejmie się recenzowania.
Rejected by reviewer - Odrzucone przez recenzenta (nie będzie recenzować lub nie zdąży zrecenzować).
Accepted by reviewer - Zaakceptowane przez recenzenta, który zobowiązał się przygotować recenzję.
Reviewed - Recenzja została zakończona (dostarczona przez recenzenta).
Not reviewed - Brak recenzji, ponieważ recenzent nie zdążył przygotować jej na czas.
'''