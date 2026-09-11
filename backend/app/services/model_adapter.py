from abc import ABC, abstractmethod
from typing import Any

from app.schemas.investigation import InvestigationTask


class ModelAdapter(ABC):
    """
    Base interface for all real remote-sensing ML models.

    Each specialist model must implement this interface.

    Examples:
        - RS-VLM
        - Captioning model
        - Grounding model
        - Change detection model
        - Optical-SAR fusion model
    """

    @abstractmethod
    def predict(
        self,
        task: InvestigationTask,
        image_paths: list[str],
        execution_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Run specialist model inference.

        Parameters
        ----------
        task:
            Investigation task selected by the Mission Agent.

        image_paths:
            Paths to the input GeoTIFF images.

        execution_context:
            Results from previous investigation tasks.
            Used when the current task depends on an
            upstream task.

        Returns
        -------
        dict
            Model output.

        Required fields
        --------------
        confidence:
            Float between 0.0 and 1.0.

        evidence:
            List of evidence dictionaries.

        Additional fields
        -----------------
        The model may return task-specific fields such as:

            VQA:
                answer

            Captioning:
                caption

            Grounding:
                regions

            Change analysis:
                change_detected
                change_type

            Optical-SAR fusion:
                finding
        """

        raise NotImplementedError