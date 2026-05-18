from abc import ABC, abstractmethod


class BaseParser(ABC):
    @abstractmethod
    def parse_price(self, url: str) -> float:
        pass