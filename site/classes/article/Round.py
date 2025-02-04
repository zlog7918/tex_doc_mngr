class Round:
    def __init__(self, id, article_id, round_number):
        self.id = id
        self.article_id = article_id
        self.round_number = round_number
        self.reviews = []

    def add_review(self, review):
        self.reviews.append(review)

    def __str__(self):
        return f"Round(id={self.id}, article_id={self.article_id}, round_number={self.round_number})"
