from abc import ABC, abstractmethod

class BaseLang(ABC):
    @property
    @abstractmethod
    def hereSomeNameForTranslatedText(self) -> str: pass