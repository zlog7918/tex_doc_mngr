from .PlLang import PlLang
from .EngLang import EngLang
from enum import Enum, member
from .ManditoryLangMembers import LangBaseEx

PL: type[LangBaseEx]=PlLang # type: ignore[type_assigment]
EN: type[LangBaseEx]=EngLang # type: ignore[type_assigment]
class LangEnum(Enum):
    pl=member(PL)
    en=member(EN)

