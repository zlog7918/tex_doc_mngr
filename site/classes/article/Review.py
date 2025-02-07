class Review:
    def __init__(self, id: int, reviewer_id: int, round_id: int, review_text: str, status: str):
        self.id = id
        self.reviewer_id = reviewer_id
        self.round_id = round_id
        self.review_text = review_text
        self.status = status

    def __str__(self):
        return f"Review(id={self.id}, round_id={self.round_id}, review_text={self.review_text})"

'''
Pending confirmation - Oczekiwanie na potwierdzenie recenzenta, że podejmie się recenzowania.
Rejected by reviewer - Odrzucone przez recenzenta (nie będzie recenzować lub nie zdąży zrecenzować).
Accepted by reviewer - Zaakceptowane przez recenzenta, który zobowiązał się przygotować recenzję.
Reviewed - Recenzja została zakończona (dostarczona przez recenzenta).
Not reviewed - Brak recenzji, ponieważ recenzent nie zdążył przygotować jej na czas.
'''