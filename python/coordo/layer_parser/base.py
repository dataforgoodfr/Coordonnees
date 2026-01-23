from abc import ABC, abstractmethod


class LayerParser(ABC):
    @abstractmethod
    def parse(self, config):
        pass
