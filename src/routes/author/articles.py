from flask_login import login_required
from flask import request, Blueprint, render_template
import controllers.article_controller as ac

articles_bp = Blueprint("articles", __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'tex'}


@articles_bp.route('/upload-form')
@login_required
def upload_form():
    return render_template('uploading_article.html')


@articles_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    title = request.form.get('title')
    editor = request.form.get('editor')
    return ac.upload_file(title, editor).to_dict()


@articles_bp.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    # TODO: If Response.error - return .to_dict()
    return ac.get_file(filename)


@articles_bp.route('/generate-preview', methods=['POST'])
@login_required
def generate_preview():
    return ac.generate_preview().to_dict()


@articles_bp.route('/temp-preview/<filename>')
@login_required
def temp_preview(filename):
    # TODO: If Response.error - return .to_dict()
    return ac.temp_preview(filename)