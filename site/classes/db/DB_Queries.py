import os
import sys
import json
import inspect
import traceback
from flask import request
from typing import Callable
from datetime import datetime,timezone

from classes.article.Review import Review
from .db_drivers.DB_Driver import DB_Driver
from ..article.Article import Article, ArticleStatus

class DB_Queries:
    def __init__(self, db_conn_fun: Callable[[],DB_Driver]):
        try:
            self.__db=db_conn_fun()
        except Exception as e:
            self.__db=None

    def get_test(self) -> str:
        try:
            ret=self.__db.query('SELECT t FROM test LIMIT 1')[0][0]
        except Exception as err:
            _,_,traceback=sys.exc_info()
            self.__log_activity(
                inspect.currentframe().f_code.co_name,
                False,
                {'err': err, 'traceback': traceback}
            )
            ret='ERROR'
        return ret
    
    def get_all_articles(self) -> list[Article]:
        try:
            results = self.__db.query('SELECT id, title, author, content, status FROM articles;')
            articles = [
                Article(
                    id=row[0],
                    title=row[1],
                    author=row[2],
                    content=row[3],
                    status=row[4]
                ) for row in results
            ]
        except Exception as err:
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
                'SELECT id, title, author, content, status FROM articles WHERE id=%(article_id)s',
                {'article_id': article_id}
            )[0]
            article = Article(
                id=result[0],
                title=result[1],
                author=result[2],
                content=result[3],
                status=result[4]
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
    
    def update_article_status(self, article_id: int, status: str) -> bool:
        try:
            self.__db.query('UPDATE articles SET status = %(status)s WHERE id = %(article_id)s;', {
                'article_id': article_id,
                'status': status
            }, False)
            print("works")
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

    def create_round(self, article_id: int, round_number: int) -> bool:
        try:
            self.__db.query('INSERT INTO rounds (article_id, round_number) VALUES (%(article_id)s, %(round_number)s);',
                            {'article_id': article_id, 'round_number': round_number}, False)
        except Exception as err:
            print("create: " + str(err))
            print("err:" + str(err))
            self.__log_activity(inspect.currentframe().f_code.co_name, False,
                                {'err': str(err), 'traceback': ''.join(traceback.format_tb(err.__traceback__))})
            return False
        return True

    def add_reviewer_to_article(self, article_id: int, reviewer_id: int, deadline_confirm: str, deadline_submit: str) -> bool:
        existing_reviews = [r for r in tmp_assigned_reviewers if r["article_id"] == article_id]
        round_number = max([r["round"] for r in existing_reviews], default=1)
        tmp_assigned_reviewers.append({
            "article_id": article_id,
            "round": round_number,
            "reviewer_id": reviewer_id,
            "deadline_confirm": deadline_confirm,
            "deadline_submit": deadline_submit
        })

        try:
            round_query = "SELECT id FROM rounds WHERE article_id = %(article_id)s ORDER BY round_number DESC LIMIT 1"
            round_result = self.__db.query(round_query, {'article_id': article_id})

            if round_result:
                round_id = round_result[0][0]
                review_query = """
                INSERT INTO reviews (round_id, reviewer_id, status, deadline_confirm, deadline_submit)
                VALUES (%(round_id)s, %(reviewer_id)s, 'Pending confirmation', %(deadline_confirm)s, %(deadline_submit)s)
                """
                self.__db.query(review_query, {
                    'round_id': round_id, 
                    'reviewer_id': reviewer_id,
                    'deadline_confirm': deadline_confirm,
                    'deadline_submit': deadline_submit
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

    def get_available_reviewers(self, article_id: int):
        assigned_ids = {r["reviewer_id"] for r in tmp_assigned_reviewers if r["article_id"] == article_id}
        return [reviewer for reviewer in tmp_reviewers if reviewer["id"] not in assigned_ids]
        try:
            return self.__db.query(
                '''
                SELECT id, name FROM reviewers 
                WHERE id NOT IN (SELECT reviewer_id FROM reviews WHERE round_id IN 
                    (SELECT id FROM rounds WHERE article_id = %(article_id)s))
                ''',
                {'article_id': article_id}, fetchall=True
            )
        except Exception as err:
            self.__log_activity(inspect.currentframe().f_code.co_name, False,
                                {'err': str(err), 'traceback': ''.join(traceback.format_tb(err.__traceback__))})
            return []
        
    def get_assigned_reviewers(self, article_id):
        return [r for r in tmp_assigned_reviewers if r["article_id"] == article_id]

    def get_articles_as_reviewer(self, reviewer_id: int) -> list[Article, int]:
        try:
            result = self.__db.query(
                '''
                SELECT a.id, a.title, a.author, a.content, a.status, r.id AS review_id
                FROM articles a
                INNER JOIN rounds ro ON a.id = ro.article_id
                INNER JOIN reviews r ON ro.id = r.round_id
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
                        author=row[2],
                        content=row[3],
                        status=row[4]
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
                SELECT r.id, r.round_id, r.review_text, r.status, r.deadline_confirm, r.deadline_submit, ro.article_id
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
                        deadline_confirm=row[4],
                        deadline_submit=row[5],
                        reviewer_id=reviewer_id,
                    ),
                    row[6]
                )
                for row in result
            ]
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

    def is_connection(self) -> bool:
        return self.__db is not None

    def __log_activity(self, action: str, is_success: bool, log: dict) -> None:
        try:
            q=self.__db.query('''
                INSERT INTO log(ip, is_success, action, timest, log) VALUES
                    (%(ip)s, %(is_success)s, %(act)s, %(timest)s, %(log)s)
            ''', {
                'ip':request.environ['REMOTE_ADDR'],
                'is_success':is_success,
                'act':action,
                'timest':self.__get_timestamp(),
                'log':json.dumps(log),
            })
        except Exception as e:
            print('<h1>Operation failed, please inform an administrator.</h1>', action, log, self.__get_timestamp())

    def __get_timestamp(self) -> datetime:
        return datetime.today().astimezone(tz=timezone.utc)

# Dane pomocnicze do wyboru recenzentów (przykładowe)
tmp_reviewers = [
    {"id": 1, "name": "Reviewer A"},
    {"id": 2, "name": "Reviewer B"},
    {"id": 3, "name": "Reviewer C"},
    {"id": 4, "name": "Reviewer D"},
]

tmp_assigned_reviewers = []