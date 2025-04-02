from sqlalchemy import and_
from ..db.db_base import db
from datetime import timedelta
from ..models.usr.User import User
from ..models.utils import utils as util
from ..models.utils.MessageException import MessageException
from ..models.usr.Code import Code, CodePurpose, CodePurposeEnum

def __get_purpose_or_err(purpose: CodePurposeEnum) -> CodePurpose:
    _purpose: CodePurpose|None=CodePurpose.query.where(CodePurpose.purpose==purpose).first()
    if _purpose is None:
        raise ValueError(f'Podany powód: {purpose.name} nie istnieje w bazie danych')
    return _purpose

def __gen_unique_code(user: User, purpose: CodePurpose) -> tuple[str, int]:
    MAX_TRIES=10
    for _ in range(MAX_TRIES):
        save_point=db.session.begin_nested()
        try:
            code, code_exp=purpose.purpose.gen_code()
            time=util.get_timestamp()
            _code=Code(**util.get_kwargs_for(Code, {
                Code.usr_id: user.id,
                Code.purpose_id: purpose.id,
                Code.code: code,
                Code.is_active: True,
                Code.timest: time,
                Code.code_exp: time+timedelta(seconds=code_exp),
            }))
            db.session.add(_code)
            save_point.commit()
            return code, code_exp
        except Exception as e:
            save_point.rollback()
            if 'unique constraint' not in str(e):
                raise e.with_traceback(e.__traceback__) from None
    raise RuntimeError(f'Nie można wylosowań unikalnego kodu pomimo {MAX_TRIES} losowań')

def gen_code(user: User, purpose: CodePurposeEnum) -> tuple[Code, int]:
    message='Nie można wygenerować kodu'
    try:
        Code.query.where(and_(
            Code.usr_id==user.id
            ,Code.is_active==True
            ,Code.code_exp<util.get_timestamp()
        )).update({Code.is_active: None})
    except Exception as e:
        raise MessageException.from_exception(e, message)
    try:
        _purpose=__get_purpose_or_err(purpose)
        code, code_exp=__gen_unique_code(user, _purpose)
        _code=Code.query.where(
            and_(
                Code.usr_id==user.id
                ,Code.purpose_id==_purpose.id
                ,Code.code==code
                ,Code.is_active==True
            )
        ).first()
        if _code is not None:
            return _code, code_exp
    except Exception as e:
        raise MessageException.from_exception(e, message)
    raise MessageException(message)

def deactivate_code(code: Code) -> None:
    try:
        code.deactivate()
        db.session.flush()
    except Exception as e:
        raise MessageException.from_exception(e, 'Nie można deaktywować kodu')

def check_code(user: User, code_str: str, purpose: CodePurposeEnum, deactivate: bool=True) -> Code|None:
    try:
        _purpose=__get_purpose_or_err(purpose)
        code=Code.query.where(
            and_(
                Code.usr_id==user.id
                ,Code.purpose_id==_purpose.id
                ,Code.code==code_str
                ,Code.is_active==True
                ,Code.code_exp>util.get_timestamp()
            )
        ).first()
        if code is None:
            return None
        if deactivate:
            deactivate_code(code)
        return code
    except Exception as e:
        raise MessageException.from_exception(e, 'Nie można potwierdzić kodu')

def active_codes(user: User, purpose: CodePurposeEnum) -> list[Code]|None:
    try:
        _purpose=__get_purpose_or_err(purpose)
        codes=Code.query.where(
            and_(
                Code.usr_id==user.id
                ,Code.purpose_id==_purpose.id
                ,Code.is_active==True
                ,Code.code_exp>util.get_timestamp()
            )
        ).all()
        if codes is None:
            return None
        return codes
    except Exception as e:
        raise MessageException.from_exception(e, 'Nie można potwierdzić kodu')
