import json
import traceback
from flask import request
from flask_sqlalchemy import SQLAlchemy
from ..models.utils.utils import get_timestamp
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



def log_activity(action: str, is_success: bool, log: dict) -> None:
    try:
        ip=request.environ['REMOTE_ADDR']
    except Exception:
        ip='local'
    db.session.add(
        Log(
            ip=ip
            ,is_success=is_success
            ,action=action
            ,timest=get_timestamp()
            ,log=json.dumps(log)
        )
    )
    db.session.commit()

def log_err(action: str, err: Exception) -> None:
    log_activity(action, False, {'err': f'{err}', 'traceback': ''.join(traceback.format_tb(err.__traceback__))})

 