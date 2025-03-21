# from six import with_metaclass
from enum import Enum, EnumMeta, _EnumDict

class _EnumCheckMemberMeta(EnumMeta):
    def __new__(cls, clsname: str, bases: tuple[type, ...], attrs: _EnumDict, base_classname: str, manditory_members: set[str]=set(), enforce_type: type|None=None):
        if base_classname!=clsname:
            members: dict[str, object]=dict(attrs._member_names) # type: ignore[type_assigment]
            members_set=set(members.keys())
            if not manditory_members.issubset(members_set):
                raise ValueError(f'Class "{clsname}" does not implement those members: {manditory_members.difference(members_set)}')
            if enforce_type is not None:
                for k in members_set:
                    if not isinstance(attrs.get(k), enforce_type):
                        print(type(attrs.get(k)))
                        print(attrs.get(k))
                        raise ValueError(f'In class "{clsname}" member "{k}" is not of type: {enforce_type.__name__}')
        return super().__new__(cls, clsname, bases, attrs)

def _getLangCheckMemberMeta(base_classname: str, manditory_members: set[str]=set(), enforce_type: type|None=None) -> type[_EnumCheckMemberMeta]:
    class meta(_EnumCheckMemberMeta):
        def __new__(cls, clsname: str, bases: tuple[type, ...], attrs: _EnumDict):
            return super().__new__(cls, clsname, bases, attrs, base_classname, manditory_members, enforce_type)
    return meta

manditory_members={'hereSomeNameForTranslatedText'}
class LangBase(Enum, metaclass=_getLangCheckMemberMeta('LangBase', manditory_members, str)):
    def __str__(self) -> str:
        return self.value