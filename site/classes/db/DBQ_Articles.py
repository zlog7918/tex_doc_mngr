import json
import random
import inspect
import traceback
from flask import request
from typing import Callable
from .DB_Queries import DB_Queries
from datetime import datetime, timezone
from classes.article.Review import Review
from .db_drivers.DB_Driver import DB_Driver
from ..utils.consts import TIME_TO_EXPIRE
from ..article.Article import Article, ArticleStatus


class DBQ_Articles(DB_Queries):
    def __init__(self, db_conn_fun: Callable[[], DB_Driver]):
        try:
            self.__db = db_conn_fun()
        except Exception as e:
            self.__db = None

    def get_user(self, nick: str) -> tuple[str, str, str, bool]:
        try:
            ret = self.__db.query('SELECT nick, email, passwd, approved FROM usr WHERE nick=%(nick)s', {'nick': nick})[
                0]
        except Exception as err:
            self.__log_activity(
                inspect.currentframe().f_code.co_name,
                False,
                {'err': f'{err}', 'traceback': ''.join(traceback.format_tb(err.__traceback__))}
            )
            raise err.with_traceback(err.__traceback__)
        return ret

    def get_articles_as_editor(self, editor_id: int) -> list[Article]:
        try:
            results = self.__db.query(
                '''
                SELECT a.id, a.author_id, a.editor_id, a.title, a.content, article_status.stat
                FROM articles a
                JOIN article_status ON a.status_id = article_status.id
                WHERE a.editor_id = %(editor_id)s;
                ''', {'editor_id': editor_id}
            )
            articles = [
                Article(
                    id=row[0],
                    author_id=row[1],
                    editor_id=row[2],
                    title=row[3],
                    content=row[4],
                    status=row[5]
                ) for row in results
            ]
        except Exception as err:
            print("Error: " + str(err))
            self.__log_activity(
                inspect.currentframe().f_code.co_name,
                False,
                {'err': f'{err}', 'traceback': ''.join(traceback.format_tb(err.__traceback__))}
            )
            return []
        return articles

    def get_article(self, article_id: int) -> Article:
        try:
            result = self.__db.query(
                '''
                SELECT a.id, title, a.author_id, a.editor_id, a.content, article_status.stat
                FROM articles a
                JOIN article_status ON a.status_id = article_status.id
                WHERE a.id=%(article_id)s;
                ''',
                {'article_id': article_id}
            )[0]
            article = Article(
                id=result[0],
                title=result[1],
                author_id=result[2],
                editor_id=result[3],
                content=result[4],
                status=result[5]
            )
        except Exception as err:
            self.__log_activity(
                inspect.currentframe().f_code.co_name,
                False,
                {'err': f'{err}', 'traceback': ''.join(traceback.format_tb(err.__traceback__))}
            )
            raise err.with_traceback(err.__traceback__)
        return article

    def add_article(self, title: str, content: str) -> bool:
        try:
            self.__db.query('''
                INSERT INTO articles(title, content, created_at) VALUES
                    (%(title)s, %(content)s, %(created_at)s)
            ''', {
                'title': title,
                'content': content,
                'created_at': self.__get_timestamp(),
            }, False)
        except Exception as err:
            self.__log_activity(
                inspect.currentframe().f_code.co_name,
                False,
                {'err': f'{err}', 'traceback': ''.join(traceback.format_tb(err.__traceback__))}
            )
            return False
        return True

    def update_article(self, article_id: int, title: str, content: str) -> bool:
        try:
            self.__db.query('''
                UPDATE articles SET
                    title=%(title)s,
                    content=%(content)s
                WHERE id=%(article_id)s
            ''', {
                'title': title,
                'content': content,
                'article_id': article_id
            }, False)
        except Exception as err:
            self.__log_activity(
                inspect.currentframe().f_code.co_name,
                False,
                {'err': f'{err}', 'traceback': ''.join(traceback.format_tb(err.__traceback__))}
            )
            return False
        return True

    def update_article_status(self, article_id: int, status: int) -> bool:
        try:
            self.__db.query('UPDATE articles SET status_id = %(status)s WHERE id = %(article_id)s;', {
                'article_id': article_id,
                'status': status
            }, False)
        except Exception as err:
            print("exception: " + str(err))
            self.__log_activity(
                inspect.currentframe().f_code.co_name,
                False,
                {'err': f'{err}', 'traceback': ''.join(traceback.format_tb(err.__traceback__))}
            )
            return False
        return True

    def delete_article(self, article_id: int) -> bool:
        try:
            self.__db.query('DELETE FROM articles WHERE id=%(article_id)s', {'article_id': article_id}, False)
        except Exception as err:
            self.__log_activity(
                inspect.currentframe().f_code.co_name,
                False,
                {'err': f'{err}', 'traceback': ''.join(traceback.format_tb(err.__traceback__))}
            )
            return False
        return True

    def get_last_round_number(self, article_id: int) -> int:
        try:
            result = self.__db.query(
                '''
                SELECT round_number FROM rounds 
                WHERE article_id = %(article_id)s
                ORDER BY round_number desc
                LIMIT 1
                ''',
                {'article_id': article_id}
            )
            if result:
                print("result:" + str(result[0]))
                return result[0]
            else:
                print("No round found, returning 0")
                return 0
        except Exception as err:
            print("Error in get_last_round_number:", err)
            self.__log_activity(inspect.currentframe().f_code.co_name, False,
                                {'err': str(err), 'traceback': ''.join(traceback.format_tb(err.__traceback__))})
            return None

    def create_round(self, article_id: int, round_number: int, deadline_confirm: str, deadline_submit: str) -> bool:
        try:
            self.__db.query('INSERT INTO rounds (article_id, round_number, q_set_id, deadline_confirm, deadline_submit) VALUES (%(article_id)s, %(round_number)s, %(q_set_id)s, %(deadline_confirm)s, %(deadline_submit)s);',
                            {'article_id': article_id, 'round_number': round_number, 'q_set_id': 1, 'deadline_confirm': deadline_confirm, 'deadline_submit': deadline_submit}, False)
        except Exception as err:
            print("create: " + str(err))
            self.__log_activity(inspect.currentframe().f_code.co_name, False,
                                {'err': str(err), 'traceback': ''.join(traceback.format_tb(err.__traceback__))})
            return False
        return True

    def add_reviewer_to_article(self, article_id: int, reviewer_id: int) -> bool:
        try:
            round_query = "SELECT id FROM rounds WHERE article_id = %(article_id)s ORDER BY round_number DESC LIMIT 1"
            round_result = self.__db.query(round_query, {'article_id': article_id})

            if round_result:
                round_id = round_result[0][0]
                review_query = """
                INSERT INTO reviews (round_id, reviewer_id, status)
                VALUES (%(round_id)s, %(reviewer_id)s, 'Pending confirmation')
                """
                self.__db.query(review_query, {
                    'round_id': round_id, 
                    'reviewer_id': reviewer_id
                }, False)
            else:
                print("round_result is None")
                # TODO
                return False

        except Exception as err:
            print("assignemnt err: " + str(err))
            self.__log_activity(
                inspect.currentframe().f_code.co_name,
                False,
                {'err': f'{err}', 'traceback': ''.join(traceback.format_tb(err.__traceback__))}
            )
            return False
        return True

    def get_available_reviewers(self, article_id: int) -> list[dict[int, str]]:
        try:
            result = self.__db.query(
                '''
                SELECT id, nick FROM usr 
                WHERE id NOT IN (SELECT reviewer_id FROM reviews WHERE round_id IN 
                    (SELECT id FROM rounds WHERE article_id = %(article_id)s ORDER BY rounds.round_number DESC LIMIT 1))
                ''',
                {'article_id': article_id}
            )
            reviewers = [{"id": row[0], "nick": row[1]} for row in result]
            return reviewers
        except Exception as err:
            print("error: " + str(err))
            self.__log_activity(inspect.currentframe().f_code.co_name, False,
                                {'err': str(err), 'traceback': ''.join(traceback.format_tb(err.__traceback__))})
            return []

    def get_assigned_reviewers(self, article_id) -> list[dict[int, str]]:
        try:
            result = self.__db.query(
                '''
                SELECT id, nick FROM usr 
                WHERE id IN (SELECT reviewer_id FROM reviews WHERE round_id IN 
                    (SELECT id FROM rounds WHERE article_id = %(article_id)s ORDER BY rounds.round_number DESC LIMIT 1))
                ''',
                {'article_id': article_id}
            )
            reviewers = [{"id": row[0], "nick": row[1]} for row in result]
            return reviewers
        except Exception as err:
            print("error: " + str(err))
            self.__log_activity(inspect.currentframe().f_code.co_name, False,
                                {'err': str(err), 'traceback': ''.join(traceback.format_tb(err.__traceback__))})
            return []
        
    def get_assigned_reviews(self, article_id) -> list[Review]:
        try:
            result = self.__db.query(
                '''
                SELECT id, reviewer_id, round_id, review_text, status
                FROM reviews 
                WHERE round_id IN 
                    (SELECT id FROM rounds WHERE article_id = %(article_id)s ORDER BY rounds.round_number DESC LIMIT 1)
                ''',
                {'article_id': article_id}
            )
            if result:
                reviews = [
                    Review(
                        id = row[0],
                        reviewer_id = row[1],
                        round_id = row[2],
                        review_text = row[3],
                        status = row[4]
                    )
                    for row in result
                ]
                return reviews
            else:
                return []
        except Exception as err:
            print("error: " + str(err))
            self.__log_activity(inspect.currentframe().f_code.co_name, False,
                                {'err': str(err), 'traceback': ''.join(traceback.format_tb(err.__traceback__))})
            return []

    def get_articles_as_reviewer(self, reviewer_id: int) -> list[Article, int]:
        try:
            result = self.__db.query(
                '''
                SELECT a.id, a.title, a.author_id, a.editor_id, a.content, article_status.stat, r.id AS review_id
                FROM articles a
                INNER JOIN rounds ro ON a.id = ro.article_id
                INNER JOIN reviews r ON ro.id = r.round_id
                JOIN article_status ON a.status_id = article_status.id
                WHERE r.reviewer_id = %(reviewer_id)s
                AND r.status IN ('Pending confirmation', 'Accepted by reviewer');
                ''',
                {'reviewer_id': reviewer_id},
            )
            return [
                (
                    Article(
                        id=row[0],
                        title=row[1],
                        author_id=row[2],
                        editor_id=row[3],
                        content=row[4],
                        status=row[5]
                    ),
                    row[5]
                )
                for row in result
            ]
        except Exception as err:
            print(f"Error: {err}")
            return []

    def get_reviews_as_reviewer(self, reviewer_id: int) -> list[Review, int]:
        try:
            result = self.__db.query(
                '''
                SELECT r.id, r.round_id, r.review_text, r.status, ro.article_id
                FROM reviews r
                INNER JOIN rounds ro ON r.round_id = ro.id
                WHERE r.reviewer_id = %(reviewer_id)s
                AND r.status IN ('Pending confirmation', 'Accepted by reviewer');
                ''',
                {'reviewer_id': reviewer_id},
            )
            return [
                (
                    Review(
                        id=row[0],
                        round_id=row[1],
                        review_text=row[2],
                        status=row[3],
                        reviewer_id=reviewer_id,
                    ),
                    row[6]
                )
                for row in result
            ]
        except Exception as err:
            print(f"Error: {err}")
            return []

    def get_review(self, article_id: int, reviewer_id: int) -> Review:
        try:
            result = self.__db.query(
                '''
                SELECT r.id, r.round_id, r.review_text, r.status
                FROM reviews r
                JOIN rounds ro ON r.round_id = ro.id
                WHERE ro.article_id = %(article_id)s
                AND r.reviewer_id = %(reviewer_id)s;
                ''',
                {'article_id': article_id, 'reviewer_id': reviewer_id},
            )[0]
            return Review(
                id=result[0],
                round_id=result[1],
                review_text=result[2],
                status=result[3],
                reviewer_id=reviewer_id,
            )
        except Exception as err:
            print(f"Error: {err}")
            return []

    def post_review(self, review: Review) -> bool:
        try:
            query = '''
                INSERT INTO reviews (review_text, round_id, reviewer_id, status)
                VALUES (%(review_text)s, %(round_id)s, %(reviewer_id)s, %(status)s)
                RETURNING id;
                '''

            params = {
                'review_text': review.review_text,
                'round_id': review.round_id,
                'reviewer_id': review.reviewer_id,
                'status': review.status,
            }
            result = self.__db.query(query, params)
            return result
        except Exception as err:
            return False

    def update_review_status(self, review_id: int, status: str) -> bool:
        try:
            self.__db.query('UPDATE reviews SET status = %(status)s WHERE id = %(review_id)s;', {
                'review_id': review_id,
                'status': status
            }, False)
        except Exception as err:
            self.__log_activity(
                inspect.currentframe().f_code.co_name,
                False,
                {'err': f'{err}', 'traceback': ''.join(traceback.format_tb(err.__traceback__))}
            )
            return False
        return True

    def get_questions_with_answers(self, q_set_id: int) -> list[dict]:
        try:
            query_questions = """
                SELECT q.id, q.question, q.is_abc 
                FROM questions q
                JOIN question_set_questions qs ON qs.question_id = q.id
                WHERE qs.question_set_id = %(q_set_id)s
            """
            questions = self.__db.query(query_questions, {'q_set_id': q_set_id})

            result = []
            for question in questions:
                question_data = {
                    "id": question[0],
                    "text": question[1],
                    "is_abc": question[2],
                    "answers": []
                }
                if question[2]:  # Jeśli is_abc = True, pobierz odpowiedzi
                    query_answers = """
                        SELECT id, answer 
                        FROM question_a 
                        WHERE question_id = %(question_id)s
                    """
                    answers = self.__db.query(query_answers, {'question_id': question[0]})
                    question_data["answers"] = [{"id": ans[0], "answer": ans[1]} for ans in answers]

                result.append(question_data)
            return result
        except Exception as err:
            print(f"Error fetching questions: {err}")
            self.__log_activity(inspect.currentframe().f_code.co_name, False,
                                {'err': str(err), 'traceback': ''.join(traceback.format_tb(err.__traceback__))})
            return []

    # def save_review_answers(self, review_id: int, answers: dict[int, str]) -> bool:
    #     try:
    #         for question_id, answer in answers.items():
    #             query_insert = """
    #                 INSERT INTO answers (review_id, question_id, answer)
    #                 VALUES (%(review_id)s, %(question_id)s, %(answer)s)
    #             """
    #             self.__db.query(query_insert, {
    #                 'review_id': review_id,
    #                 'question_id': question_id,
    #                 'answer': answer
    #             }, commit=False)
    #         self.__db.commit()
    #         return True
    #     except Exception as err:
    #         print(f"Error saving answers: {err}")
    #         self.__log_activity(inspect.currentframe().f_code.co_name, False,
    #                             {'err': str(err), 'traceback': ''.join(traceback.format_tb(err.__traceback__))})
    #         return False

    def save_review_answers(self, review_id: int, answers: dict[int, str]) -> bool:
        try:
            for question_id, answer in answers.items():
                query_insert = """
                    INSERT INTO answers (review_id, question_id, answer)
                    VALUES (%(review_id)s, %(question_id)s, %(answer)s)
                """
                self.__db.query(query_insert, {
                    'review_id': review_id,
                    'question_id': question_id,
                    'answer': answer
                }, False)
            
            # Update the review status to 'Reviewed'
            query_update_status = """
                UPDATE reviews
                SET status = 'Reviewed'
                WHERE id = %(review_id)s
            """
            self.__db.query(query_update_status, {'review_id': review_id}, False)
            
            return True
        except Exception as err:
            print(f"Error saving answers: {err}")
            self.__log_activity(inspect.currentframe().f_code.co_name, False,
                                {'err': str(err), 'traceback': ''.join(traceback.format_tb(err.__traceback__))})
            return False

    def get_questions_by_article(self, article_id: int):
        try:
            # TODO: check if this is the right round
            query = """
                SELECT q.id, q.question, q.is_abc
                FROM questions q
                JOIN question_set_questions qsq ON q.id = qsq.question_id
                JOIN question_set qs ON qsq.question_set_id = qs.id
            """
            result = self.__db.query(query, {'article_id': article_id})
            if result:
                questions = [{"id": row[0], "text": row[1], "is_abc": row[2]} for row in result]
                return questions
            else:
                return []
        except Exception as err:
            print(f"Error get questions: {err}")
            self.__log_activity(inspect.currentframe().f_code.co_name, False,
                                {'err': str(err), 'traceback': ''.join(traceback.format_tb(err.__traceback__))})
            return None 

    def get_question_answers(self, question_id: int):
        query = """
            SELECT id, answer
            FROM question_a
            WHERE question_id = %(question_id)s
        """
        result = self.__db.query(query, {'question_id': question_id})
        if result:
            answers = [{"id": row[0], "answer": row[1]} for row in result]
            return answers
        else:
            return []

    def is_connection(self) -> bool:
        return self.__db is not None

    def __log_activity(self, action: str, is_success: bool, log: dict) -> None:
        try:
            self.__db.query('''
                INSERT INTO log(ip, is_success, "action", timest, "log") VALUES
                    (%(ip)s, %(is_success)s, %(act)s, %(timest)s, %(log)s)
            ''', {
                'ip': request.environ['REMOTE_ADDR'],
                'is_success': is_success,
                'act': action,
                'timest': self.__get_timestamp(),
                'log': json.dumps(log),
            }, False)
        except Exception as e:
            print('<h1>Operation failed, please inform an administrator.</h1>', action, log, self.__get_timestamp())

    def __get_timestamp(self) -> datetime:
        return datetime.today().astimezone(tz=timezone.utc)
