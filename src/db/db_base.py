import json
from flask import request
from flask_sqlalchemy import SQLAlchemy
from ..models.utils import utils as util
from sqlalchemy import MetaData, Integer, Boolean, Text, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    metadata = MetaData(naming_convention={
        "ix": 'ix_%(column_0_label)s',
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    })

db = SQLAlchemy(model_class=Base)

class Log(db.Model):
    __tablename__ = 'log'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ip: Mapped[str] = mapped_column(Text, nullable=False)
    is_success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    timest: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    log: Mapped[str] = mapped_column(Text, nullable=False)


def __get_action_name(action: str|None) -> str:
    return (util.get_function(2) if action is None else action)
def log_activity(is_success: bool, log: dict, action: str|None=None) -> None:
    try:
        ip=request.environ['REMOTE_ADDR']
    except Exception:
        ip='local'
    db.session.add(
        Log(**util.get_kwargs_for(Log, {
            Log.ip: ip,
            Log.is_success: is_success,
            Log.action: __get_action_name(action),
            Log.timest: util.get_timestamp(),
            Log.log: json.dumps(log),
        }))
    )
    db.session.flush()

def log_err(err: Exception, action: str|None=None) -> None:
    log_activity(False, {
        'err': f'{err}',
        'traceback': util.get_traceback(err)
    }, action=__get_action_name(action))
 