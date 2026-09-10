from abc import ABC, abstractmethod

from app.schemas.investigation import InvestigationTask


class ModelAdapter(ABC):

    @abstractmethod
    def predict(self, task: InvestigationTask) -> dict:
        """
        Run the specialist model for the given investigation task.

        The ML developer will implement this method
        for the real remote-sensing model.
        """
        pass