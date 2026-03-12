"""ML model interface for loading and inference"""

import logging
from pathlib import Path

import joblib
import numpy as np

logger = logging.getLogger(__name__)


class AnomalyModel:
    """Interface for anomaly detection ML model"""

    def __init__(self, model_path: str):
        """Initialize model from file path"""
        self.model_path = Path(model_path)
        self.model = None
        self.loaded = False
        self.load_model()

    def load_model(self):
        """Load pre-trained model from disk"""
        try:
            if self.model_path.exists():
                self.model = joblib.load(self.model_path)
                self.loaded = True
                logger.info(f"Loaded model from {self.model_path}")
            else:
                logger.warning(f"Model file not found: {self.model_path}")
                self.loaded = False
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.loaded = False

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Run model inference.

        Args:
            X: Input features array

        Returns:
            Array of anomaly scores (0-1 for Isolation Forest)
        """
        if not self.loaded or self.model is None:
            raise RuntimeError("Model not loaded")

        try:
            # Isolation Forest returns -1 for anomalies, 1 for normal
            # Convert to 0-1 score: anomaly=1, normal=0
            predictions = self.model.predict(X)
            scores = np.where(predictions == -1, 1.0, 0.0)

            # Try to get anomaly scores if available
            if hasattr(self.model, 'score_samples'):
                raw_scores = self.model.score_samples(X)
                # Normalize to 0-1 range based on quantiles
                scores = self._normalize_scores(raw_scores)

            return scores
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            raise

    def _normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        """Normalize raw scores to 0-1 range"""
        # Min-max normalization based on data range
        min_score = np.percentile(scores, 5)
        max_score = np.percentile(scores, 95)

        normalized = (scores - min_score) / (max_score - min_score)
        normalized = np.clip(normalized, 0, 1)
        return normalized

    def reload_model(self):
        """Reload model from disk (e.g., when new version is deployed)"""
        logger.info(f"Reloading model from {self.model_path}")
        self.load_model()
