from models.usr import User as U
from flask import abort, Blueprint, request
import controllers.question_controller as qc
from models.utils.FormNotFilledException import FormNotFilledException
from models.utils import decors as decor, utils as util, utils_flask as f_util

questions_bp=Blueprint('question', __name__)

@questions_bp.route('/')
@decor.group_required(U.UserGroupEnum.Editor)
def show_selection():
    return f_util.render_base_template('questions/selection.html')

@questions_bp.route('/q')
@decor.group_required(U.UserGroupEnum.Editor)
def show_questions():
    ret=qc.get_all_questions()
    return f_util.render_base_template('questions/questions_view.html', questions=ret.data)
@questions_bp.route('/q_j', methods=['GET', 'POST'])
@decor.group_required(U.UserGroupEnum.Editor)
def show_questions_json():
    ret=qc.get_all_questions()
    return ret.to_dict()

@questions_bp.route('/q/<int:question_id>')
@decor.group_required(U.UserGroupEnum.Editor)
def question_details(question_id: int):
    ret=qc.get_question(question_id)
    if ret.success:
        return f_util.render_base_template('questions/question_view.html', question=ret.data)
    else:
        abort(404)
@questions_bp.route('/q_j/<int:question_id>', methods=['GET', 'POST'])
@decor.group_required(U.UserGroupEnum.Editor)
def question_details_json(question_id: int):
    ret=qc.get_question(question_id)
    return ret.to_dict()

@questions_bp.route('/q_add', methods=['GET'])
@decor.group_required(U.UserGroupEnum.Editor)
@decor.handle_form_not_filled
def question_add_v():
    return f_util.render_base_template('questions/question_add.html')
@questions_bp.route('/q_add', methods=['POST'])
@decor.group_required(U.UserGroupEnum.Editor)
@decor.handle_form_not_filled
def question_add():
    (question, is_abcd)=util.get_from_form(request.form, (
        'question',
        'is_abcd',
    ))
    is_abcd=is_abcd.lower() in {'y', 'yes'}
    abc_s=request.form.getlist('abcd')
    if is_abcd:
        if len(abc_s)==0:
            lang_pkg=util.get_lang_pkg()
            raise FormNotFilledException(lang_pkg.FormDoesNotContain.value('abcd'))
    else:
        abc_s=None
    return qc.cr_question(question, abc_s).to_dict()

@questions_bp.route('/qg')
@decor.group_required(U.UserGroupEnum.Editor)
def show_question_groups():
    ret=qc.get_all_question_groups()
    return f_util.render_base_template('questions/question_groups_view.html', question_groups=ret.data)
@questions_bp.route('/qg_j', methods=['GET', 'POST'])
@decor.group_required(U.UserGroupEnum.Editor)
def show_question_groups_json():
    ret=qc.get_all_question_groups()
    return ret.to_dict()

@questions_bp.route('/qg/<int:question_group_id>')
@decor.group_required(U.UserGroupEnum.Editor)
def question_group_details(question_group_id: int):
    ret=qc.get_question_group(question_group_id)
    if ret.success:
        return f_util.render_base_template('questions/question_group_view.html', question_group=ret.data)
    else:
        abort(404)
@questions_bp.route('/qg_j/<int:question_group_id>', methods=['GET', 'POST'])
@decor.group_required(U.UserGroupEnum.Editor)
def question_group_details_json(question_group_id: int):
    ret=qc.get_question_group(question_group_id)
    return ret.to_dict()

@questions_bp.route('/qg_add', methods=['GET'])
@decor.group_required(U.UserGroupEnum.Editor)
@decor.handle_form_not_filled
def question_group_add_v():
    ret=qc.get_all_questions()
    questions=ret.data
    if not ret.success:
        questions=[]
    return f_util.render_base_template('questions/question_group_add.html', questions=questions)
@questions_bp.route('/qg_add', methods=['POST'])
@decor.group_required(U.UserGroupEnum.Editor)
@decor.handle_form_not_filled
def question_group_add():
    qg_name,=util.get_from_form(request.form, ('name',))
    questions=request.form.getlist('question')
    lang_pkg=util.get_lang_pkg()
    if len(questions)==0:
        raise FormNotFilledException(lang_pkg.FormDoesNotContain.value('question'))
    try:
        question_ids=[int(q) for q in questions]
    except:
        raise FormNotFilledException(lang_pkg.FormDoesNotContain.value('question'))
    return qc.cr_question_group(qg_name, question_ids).to_dict()
