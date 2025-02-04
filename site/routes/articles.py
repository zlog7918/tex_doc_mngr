from flask import Blueprint, jsonify, render_template
from flask import request, redirect, url_for
from classes.article import Article
from classes.db import DB_Factory, DB_Queries
from classes.db.DB_Factory import DB_Factory, DB_QueriesOpt
articles_bp = Blueprint("articles", __name__, template_folder="templates")

'''
Submitted - artykół przesłany przez autora - nowy lub poprawiony
Accepted - zweryfikownay przez edytora, gotowy do recenzji
In review - przesłany do recenzentów, oczekujący na recenzje
Reviewed - przesłane wszystkie recenzje/zakończył się czas na recenzje
Rejected - odrzucony
Needs Corrections - wymaga poprawek, czeka na poprawki autora
Final - artykół jest zakończony, nie wymaga poprawek, wersja końcowa
'''

@articles_bp.route('/')
def show_articles():
    db: DB_Queries=DB_Factory.get_db(DB_QueriesOpt.DB_Queries)
    try:
        articles = db.get_all_articles()
    except Exception as err:
        return str(err), 500
    return render_template("articles.html", articles=articles)

@articles_bp.route('/<int:article_id>')
def article_details(article_id):
    db: DB_Queries=DB_Factory.get_db(DB_QueriesOpt.DB_Queries)
    try:
        article = db.get_article(article_id)
    except Exception as err:
        return str(err), 500
    if not article:
        return "Article not found", 404

    if article.status == "Submitted":
        return render_template("article_submitted.html", article=article)

    # Renderowanie odpowiedniego szablonu dla treści zakładki
    if article.status == "Accepted":
        reviewers = db.get_available_reviewers(article_id)
        assigned_reviewers = db.get_assigned_reviewers(article_id)
        tab_content = render_template("round_tabs/accepted.html", article=article, reviewers=reviewers, assigned_reviewers=assigned_reviewers)
    elif article.status == "In review":
        reviews_remaining = 3
        if article.rounds:
            reviews_remaining = 3 - len(article["rounds"][-1]["reviews"]) if article["rounds"] else 3
        tab_content = render_template("round_tabs/in_review.html", article=article, reviews_remaining=reviews_remaining)
    elif article.status == "Reviewed":
        tab_content = render_template("round_tabs/reviewed.html", article=article)
    else:
        tab_content = "<p>No content available for this status.</p>"

    return render_template("article_reviewed.html", article=article, tab_content=tab_content)

@articles_bp.route('/<int:article_id>/accept', methods=['POST'])
def accept_article(article_id):
    db: DB_Queries = DB_Factory.get_db(DB_QueriesOpt.DB_Queries)
    try:
        article = db.get_article(article_id)
        if not article:
            return "Article not found", 404
        
        # Zmiana statusu na 'Accepted'
        result = db.update_article_status(article_id, "Accepted")
        if not result:
            return {"warning": "Article status not updated"}, 500

        # Pobranie numeru ostatniej rundy dla artykułu
        last_round_number = db.get_last_round_number(article_id)

        if last_round_number is not None:
            new_round_number = last_round_number + 1
            result = db.create_round(article_id, new_round_number)
            print("result")
            if not result:
                print("not result")
                return {"warning": "New round not created"}, 500
        else:
            print("else")
            return {"warning": "New round not created"}, 500

        return {"message": f"Article status updated to Accepted. New round {new_round_number} created."}, 200

    except Exception as err:
        return {"error": str(err)}, 500

@articles_bp.route('/<int:article_id>/add_round', methods=['POST'])
def add_round(article_id):
    db: DB_Queries = DB_Factory.get_db(DB_QueriesOpt.DB_Queries)
    article = db.get_article(article_id)
    if not article:
        return jsonify({"success": False}), 404

    # Sprawdzanie, czy artykuł spełnia wymagane statusy
    if article.status not in ["Accepted", "In review", "Reviewed"]:
        return jsonify({"success": False}), 400

    # Dodawanie nowej rundy
    new_round_id = len(article.rounds) + 1
    new_round = {"id": new_round_id, "reviews": []}
    article.rounds.append(new_round)
    return jsonify({"success": True})

@articles_bp.route('/assign_reviewers/<int:article_id>', methods=['POST'])
def assign_reviewers(article_id):
    db: DB_Queries = DB_Factory.get_db(DB_QueriesOpt.DB_Queries)
    
    # Pobieranie wybranych recenzentów z formularza
    selected_reviewer = request.form.get('reviewer')
    deadline_confirm = request.form.get('deadline_confirm')
    deadline_submit = request.form.get('deadline_submit')
    
    if not selected_reviewer:
        return "No reviewer selected", 400
    
    try:
        db.add_reviewer_to_article(article_id, int(selected_reviewer), deadline_confirm, deadline_submit)
        return redirect(url_for('articles.article_details', article_id=article_id))
    except Exception as err:
        return str(err), 500

@articles_bp.route('/<int:article_id>/reject', methods=['POST'])
def reject_article(article_id):
    db: DB_Queries = DB_Factory.get_db(DB_QueriesOpt.DB_Queries)
    article = db.get_article(article_id)
    if not article:
        return jsonify({"success": False}), 404

    # Oznaczanie artykułu jako odrzucony
    result = db.update_article_status(article_id, "Rejected")
    return jsonify({"success": True})

@articles_bp.route('/<int:article_id>/update_status', methods=['POST'])
def update_article_status(article_id):
    db: DB_Queries = DB_Factory.get_db(DB_QueriesOpt.DB_Queries)
    try:
        article = db.get_article(article_id)
        if not article:
            return {"error": "Article not found"}, 404

        current_status = article["status"]

        # Sprawdzenie obecnego statusu i zmiana
        if current_status == "Accepted":
            # Ustawienie statusu na "In review"
            result = db.update_article_status(article_id, "In review")
            if not result:
                return {"error": "Failed to update status to 'In review'"}, 500

            # Tworzenie nowej rundy recenzji
            new_round_id = len(article["rounds"]) + 1
            new_round = {"id": new_round_id, "reviews": []}
            article["rounds"].append(new_round)
            db.save_article_rounds(article_id, article["rounds"])

            return {"message": "Status updated to 'In review' and new review round created"}, 200

        elif current_status == "In review":
            # Sprawdzenie liczby przesłanych recenzji
            latest_round = article["rounds"][-1] if article["rounds"] else None
            if not latest_round:
                return {"error": "No active review round found"}, 400

            total_reviews = len(latest_round["reviews"])
            if total_reviews >= 3:  # Zakładamy, że wymagane są 3 recenzje
                result = db.update_article_status(article_id, "Reviewed")
                if result:
                    return {"message": "All reviews submitted. Status updated to 'Reviewed'"}, 200
                else:
                    return {"error": "Failed to update status to 'Reviewed'"}, 500
            else:
                remaining = 3 - total_reviews
                return {"message": f"Waiting for {remaining} more reviews"}, 200

        else:
            return {"error": "Invalid status for update"}, 400

    except Exception as err:
        return {"error": str(err)}, 500