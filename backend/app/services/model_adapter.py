from abc import ABC, abstractmethod

from app.schemas.investigation import InvestigationTask


class ModelAdapter(ABC):

    @abstractmethod
    def predict(
        self,
        task: InvestigationTask,
        image_paths: list[str],
    ) -> dict:
        """
        Run the specialist remote-sensing model.

        Parameters:
            task:
                Investigation task selected by SatQuery.

            image_paths:
                Paths to the input GeoTIFF images.

        Returns:
            A dictionary containing the model output,
            confidence, and evidence.
        """
        pass