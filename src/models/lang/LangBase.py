from enum import Enum, EnumMeta, _EnumDict
from .ManditoryLangMembers import LangBaseEx

class _EnumCheckMemberMeta(EnumMeta):
    def __new__(cls, clsname: str, bases: tuple[type, ...], attrs: _EnumDict, base_classname: str, manditory_members_and_types: dict[str, type]=dict(), enforce_type: tuple[type, ...]|None=None):
        if base_classname!=clsname:
            members: dict[str, object]={k:attrs.get(k) for k in attrs._member_names.keys()} # type: ignore[private]
            members_set=set(members.keys())
            manditory_members=set(manditory_members_and_types.keys())
            if not manditory_members.issubset(members_set):
                raise ValueError(f'Class "{clsname}" does not implement those members: {manditory_members.difference(members_set)}')
            for k in manditory_members:
                enf_type_s=manditory_members_and_types[k]
                if not isinstance(members[k], enf_type_s):
                    if isinstance(enf_type_s, tuple):
                        enforce_type_name='" or "'.join([enf.__name__ for enf in enf_type_s])
                    else:
                        enforce_type_name=enf_type_s.__name__
                    raise ValueError(f'In class "{clsname}" member "{k}" is not of type: "{enforce_type_name}"')
            if enforce_type is not None:
                for k in members_set.difference(manditory_members):
                    if not isinstance(members[k], enforce_type):
                        enforce_type_name='" or "'.join([enf.__name__ for enf in enforce_type])
                        raise ValueError(f'In class "{clsname}" member "{k}" is not of type: "{enforce_type_name}"')
        return super().__new__(cls, clsname, bases, attrs)

def _getLangCheckMemberMeta(base_classname: str, manditory_members: type[Enum]=EnumMeta('enum', (Enum, ), EnumMeta.__prepare__('enum', (Enum, )))) -> type[_EnumCheckMemberMeta]:
    d=manditory_members._member_map_
    manditory_members_and_types={k:type(v.value) for k,v in d.items()}
    class meta(_EnumCheckMemberMeta):
        def __new__(cls, clsname: str, bases: tuple[type, ...], attrs: _EnumDict):
            return super().__new__(cls, clsname, bases, attrs, base_classname, manditory_members_and_types)
    return meta

class LangBase(Enum, metaclass=_getLangCheckMemberMeta('LangBase', LangBaseEx)):
    def __str__(self) -> str:
        return self.value
