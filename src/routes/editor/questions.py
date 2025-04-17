from flask import abort, Blueprint, request
import controllers.question_controller as qc
from models.utils import decors as decor, utils as util
from models.utils.FormNotFilledException import FormNotFilledException

questions_bp=Blueprint('question', __name__)

@questions_bp.route('/')
@decor.approve_required
def show_selection():
    return util.render_base_template('questions/selection.html')

@questions_bp.route('/q')
@decor.approve_required
def show_questions():
    ret=qc.get_all_questions()
    return util.render_base_template('questions/questions_view.html', questions=ret.data)
@questions_bp.route('/q_j', methods=['GET', 'POST'])
@decor.approve_required
def show_questions_json():
    ret=qc.get_all_questions()
    return ret.to_dict()

@questions_bp.route('/q/<int:question_id>')
@decor.approve_required
def question_details(question_id: int):
    ret=qc.get_question(question_id)
    if ret.success:
        return util.render_base_template('questions/question_view.html', question=ret.data)
    else:
        abort(404)
@questions_bp.route('/q_j/<int:question_id>', methods=['GET', 'POST'])
@decor.approve_required
def question_details_json(question_id: int):
    ret=qc.get_question(question_id)
    return ret.to_dict()

@questions_bp.route('/q_add', methods=['GET'])
@decor.approve_required
@decor.handle_form_not_filled
def question_add_v():
    return util.render_base_template('questions/question_add.html')
@questions_bp.route('/q_add', methods=['POST'])
@decor.approve_required
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
@decor.approve_required
def show_question_groups():
    ret=qc.get_all_question_groups()
    return util.render_base_template('questions/question_groups_view.html', question_groups=ret.data)
@questions_bp.route('/qg_j', methods=['GET', 'POST'])
@decor.approve_required
def show_question_groups_json():
    ret=qc.get_all_question_groups()
    return ret.to_dict()

@questions_bp.route('/qg/<int:question_group_id>')
@decor.approve_required
def question_group_details(question_group_id: int):
    ret=qc.get_question_group(question_group_id)
    if ret.success:
        return util.render_base_template('questions/question_group_view.html', question_group=ret.data)
    else:
        abort(404)
@questions_bp.route('/qg_j/<int:question_group_id>', methods=['GET', 'POST'])
@decor.approve_required
def question_group_details_json(question_group_id: int):
    ret=qc.get_question_group(question_group_id)
    return ret.to_dict()

@questions_bp.route('/qg_add', methods=['GET'])
@decor.approve_required
@decor.handle_form_not_filled
def question_group_add_v():
    ret=qc.get_all_questions()
    questions=ret.data
    if not ret.success:
        questions=[]
    return util.render_base_template('questions/question_group_add.html', questions=questions)
@questions_bp.route('/qg_add', methods=['POST'])
@decor.approve_required
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

@questions_bp.route('/qs')
@decor.approve_required
def show_question_sets():
    ret=qc.get_all_question_sets()
    return util.render_base_template('questions/question_sets_view.html', question_sets=ret.data)
@questions_bp.route('/qs_j', methods=['GET', 'POST'])
@decor.approve_required
def show_question_sets_json():
    ret=qc.get_all_question_sets()
    return ret.to_dict()

@questions_bp.route('/qs/<int:question_set_id>')
@decor.approve_required
def question_set_details(question_set_id: int):
    ret=qc.get_question_set(question_set_id)
    if ret.success:
        return util.render_base_template('questions/question_set_view.html', question_set=ret.data)
    else:
        abort(404)
@questions_bp.route('/qs_j/<int:question_set_id>', methods=['GET', 'POST'])
@decor.approve_required
def question_set_details_json(question_set_id: int):
    ret=qc.get_question_set(question_set_id)
    return ret.to_dict()

@questions_bp.route('/qs_add', methods=['GET'])
@decor.approve_required
@decor.handle_form_not_filled
def question_set_add_v():
    ret=qc.get_all_question_groups()
    question_groups=ret.data
    if not ret.success:
        question_groups=[]
    return util.render_base_template('questions/question_set_add.html', question_groups=question_groups)
@questions_bp.route('/qs_add', methods=['POST'])
@decor.approve_required
@decor.handle_form_not_filled
def question_set_add():
    qg_name,=util.get_from_form(request.form, ('name',))
    question_groups=request.form.getlist('question_group')
    lang_pkg=util.get_lang_pkg()
    if len(question_groups)==0:
        raise FormNotFilledException(lang_pkg.FormDoesNotContain.value('question_group'))
    try:
        question_group_ids=[int(q) for q in question_groups]
    except:
        raise FormNotFilledException(lang_pkg.FormDoesNotContain.value('question_group'))
    return qc.cr_question_set(qg_name, question_group_ids).to_dict()
