from enum import Enum

class ArticleStatus(Enum):
    SUBMITTED = "Submitted"
    ACCEPTED = "Accepted"
    IN_REVIEW = "In review"
    REVIEWED = "Reviewed"
    REJECTED = "Rejected"
    NEEDS_CORRECTIONS = "Needs Corrections"
    FINAL = "Final"

class Article:
    def __init__(self, id: int, author_id: int, editor_id: int|None, title: str, content: str, status: str):
        self.id = id
        self.author_id = author_id
        self.editor_id = editor_id
        self.title = title
        self.content = content
        self.status = status
        self.rounds = []

    def add_round(self, round):
        self.rounds.append(round)

    def __str__(self):
        return f"Article(id={self.id}, title={self.title}, author={self.author_id}, content={self.content}, status={self.status})"