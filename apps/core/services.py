from abc import ABC, abstractmethod


class Service(ABC):
    @abstractmethod
    def execute(self):
        """Executa a operação de negócio."""
        raise NotImplementedError
