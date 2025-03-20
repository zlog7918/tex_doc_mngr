from flask_login import login_required
import controllers.user_controller as uc
from flask import Blueprint, redirect, request
from models.utils import decors as decor, utils as util
from models.utils.FormNotFilledException import FormNotFilledException

user_bp = Blueprint('user', __name__)

@user_bp.route('/login', methods=['POST'])
@decor.handle_form_not_filled
def login():
    t=util.get_from_form(request.form, (
        'nick',
        'passwd'
    ))
    return uc.login(*t).to_dict()


@user_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    return uc.logout().to_dict()


@user_bp.route('/signup', methods=['POST'])
@decor.handle_form_not_filled
def signup():
    t=util.get_from_form(request.form, (
        'nick',
        'email',
        'passwd',
        'rep_passwd',
    ))
    return uc.signup_user(*t).to_dict()


@user_bp.route('/approve/<email>/<code>', methods=['GET', 'POST'])
def approve(email: str, code: str):
    ret=uc.approve(email, code)
    if ret.success:
        return redirect('/')
    # return util.render_base_template('error.html', err=ret.to_dict())
    return ret.to_dict()

@user_bp.route('/ch_pass', methods=['POST'])
@login_required
@decor.handle_form_not_filled
def ch_pass():
    t=util.get_from_form(request.form, (
        'passwd',
        'new_passwd',
        'rep_passwd',
    ))
    return uc.change_password(*t).to_dict()

@user_bp.route('/pass_reset', methods=['POST'])
@decor.handle_form_not_filled
def pass_reset_request():
    email,=util.get_from_form(request.form, (
        'email',
    ))
    try:
        code,=util.get_from_form(request.form, (
            'code',
        ))
    except FormNotFilledException as e:
        return uc.request_pass_reset(email).to_dict()
    t=util.get_from_form(request.form, (
        'passwd',
        'rep_passwd',
    ))
    return uc.pass_reset_new_pass(email, code, *t).to_dict()

@user_bp.route('/pass_reset/<email>/<code>', methods=['GET', 'POST'])
def pass_reset(email: str, code: str):
    ret=uc.pass_reset(email, code)
    if ret.success:
        return util.render_base_template('pass_reset.html', email=email, code=ret.data)
    # return util.render_base_template('error.html', err=ret.to_dict())
    return ret.to_dict()

@user_bp.route('/create_inv', methods=['POST'])
@decor.approve_required
@decor.handle_form_not_filled
def create_invitation():
    email,=util.get_from_form(request.form, (
        'email',
    ))
    return uc.invite_user(email).to_dict()

# TODO: after check, delete this func
@user_bp.route('/create_inv_form')
@decor.approve_required
def create_invitation_form():
    return util.render_base_template('create_inv_form.html')

@user_bp.route('/accept_inv/<email>/<code>', methods=['GET', 'POST'])
def accept_invitation(email: str, code: str):
    ret=uc.accept_invite(email, code)
    if ret.success:
        return util.render_base_template('cr_user.html', email=email, code=ret.data)
    # return util.render_base_template('error.html', err=ret.to_dict())
    return ret.to_dict()

@user_bp.route('/accept_inv', methods=['POST'])
@decor.handle_form_not_filled
def accept_invitation_cr_user():
    t=util.get_from_form(request.form, (
        'email',
        'code',
        'nick',
        'passwd',
        'rep_passwd',
    ))
    return uc.accept_invite_cr_user(*t).to_dict()

@user_bp.route('/pass_reset_form')
def pass_reset_form():
    return util.render_base_template('request_pass_change.html')
