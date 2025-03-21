from .PlLang import PlLang
from .EngLang import EngLang
from enum import Enum, member
from .LangBase import LangBase

class LangEnum(Enum):
    PL=member(PlLang)
    EN=member(EngLang)

# https://stackoverflow.com/questions/71470802/how-do-i-specify-an-enum-type-hint-for-a-flask-route-parameter
