"""Anomaly detection service with statistical and ML methods"""

import logging
from datetime import datetime, timedelta

import numpy as np
from sqlalchemy.orm import Session

from src.ml.anomaly_model import AnomalyModel
from src.models import AnomalyDetectionResult, CauseEnum, ResultEnum, Transaction
from src.schemas.anomaly import SeverityEnum

logger = logging.getLogger(__name__)


class AnomalyDetectionService:
    """Hybrid anomaly detection using statistical and ML methods"""

    # Hybrid detection weights
    STATS_WEIGHT = 0.4
    ML_WEIGHT = 0.6

    # Thresholds
    STATS_THRESHOLD = 8  # Modified Z-score threshold
    ML_THRESHOLD = 0.7  # Isolation Forest anomaly score
    COMBINED_THRESHOLD = 0.5  # Combined score threshold

    # Severity thresholds
    SEVERITY_MEDIUM = 0.6
    SEVERITY_HIGH = 0.8

    def __init__(self, model: AnomalyModel):
        """Initialize with loaded ML model"""
        self.model = model

    def detect_anomalies(
        self,
        db: Session,
        transactions: list[Transaction],
        model_version: str,
    ) -> list[tuple[Transaction, AnomalyDetectionResult]]:
        """
        Detect anomalies using hybrid approach (statistical + ML).

        Args:
            db: Database session
            transactions: List of Transaction objects to analyze
            model_version: Model version identifier for audit trail

        Returns:
            List of (transaction, result) tuples
        """
        if not transactions:
            return []

        # Group by category for statistical analysis
        category_groups = {}
        for txn in transactions:
            if txn.category not in category_groups:
                category_groups[txn.category] = []
            category_groups[txn.category].append(txn)

        results = []

        for category, txns in category_groups.items():
            # Get historical transactions for statistical baseline
            historical = self._get_historical_transactions(db, category)

            # Prepare data
            amounts = np.array([t.amount for t in txns]).reshape(-1, 1)

            # Statistical detection
            stats_scores = self._statistical_detection(amounts, historical)

            # ML detection
            ml_scores = self._ml_detection(amounts)

            # Hybrid fusion
            for i, txn in enumerate(txns):
                stats_score = float(stats_scores[i])
                ml_score = float(ml_scores[i])
                combined_score = (
                    self.STATS_WEIGHT * stats_score + self.ML_WEIGHT * ml_score
                )

                # Classify result
                is_anomaly = combined_score >= self.COMBINED_THRESHOLD
                result = ResultEnum.ANOMALY if is_anomaly else ResultEnum.NORMAL

                # Classify cause
                cause = self._classify_cause(stats_score, ml_score, combined_score)

                # Generate explanation
                explanation, advice = self._generate_explanations(
                    txn, stats_score, ml_score, combined_score, cause
                )

                # Determine severity
                severity = self._determine_severity(combined_score)

                # Create result object
                detection_result = AnomalyDetectionResult(
                    transaction_id=txn.transaction_id,
                    stats_score=stats_score,
                    ml_score=ml_score,
                    combined_score=combined_score,
                    result=result,
                    base_explanation=explanation,
                    cause=cause,
                    advice=advice,
                    model_version=model_version,
                )

                results.append((txn, detection_result, severity))

        return results

    def _get_historical_transactions(
        self, db: Session, category: str, days: int = 12
    ) -> np.ndarray:
        """Get historical transaction amounts for baseline calculation"""
        cutoff_date = datetime.utcnow().date() - timedelta(days=days)
        historical = (
            db.query(Transaction.amount)
            .filter(
                Transaction.category == category,
                Transaction.date >= cutoff_date,
            )
            .all()
        )
        return np.array([t[0] for t in historical]) if historical else np.array([])

    def _statistical_detection(
        self, amounts: np.ndarray, historical: np.ndarray
    ) -> np.ndarray:
        """
        Statistical anomaly detection using Modified Z-score.

        Uses Median Absolute Deviation (MAD) for robust outlier detection.
        Formula: modified_zscore = 0.6745 * (x - median) / MAD
        Threshold: |zscore| > 8
        """
        if len(historical) < 2:
            # Default to 0.3 score if insufficient history
            return np.full(len(amounts), 0.3)

        # Calculate robust statistics
        median = np.median(historical)
        mad = np.median(np.abs(historical - median))

        if mad == 0:
            mad = 1  # Prevent division by zero

        # Calculate modified Z-scores
        zscore = 0.6745 * (amounts.flatten() - median) / (mad + 1e-8)

        # Convert to anomaly score (0-1)
        # Threshold at 8, normalize to 0-1 scale
        anomaly_score = np.minimum(np.abs(zscore) / self.STATS_THRESHOLD, 1.0)

        return anomaly_score

    def _ml_detection(self, amounts: np.ndarray) -> np.ndarray:
        """
        ML-based anomaly detection using Isolation Forest.

        Returns normalized anomaly scores (0-1) where 1 is max anomaly.
        """
        if not self.model.loaded:
            logger.warning("ML model not loaded, returning default scores")
            return np.full(len(amounts), 0.5)

        try:
            # Feature engineering: create window features for time-series context
            # In production, this would include window statistics
            features = self._engineer_features(amounts)

            # Run inference
            scores = self.model.predict(features)

            return scores
        except Exception as e:
            logger.error(f"ML detection error: {e}")
            return np.full(len(amounts), 0.5)

    def _engineer_features(self, amounts: np.ndarray) -> np.ndarray:
        """Engineer features for ML model"""
        # Simple implementation: use amount as feature
        # In production, would include window statistics (mean, std, slope, etc.)
        features = amounts.reshape(-1, 1)
        return features

    def _classify_cause(
        self, stats_score: float, ml_score: float, combined_score: float
    ) -> CauseEnum:
        """
        Classify anomaly cause based on detection method scores.

        STATISTICAL_SPIKE: High stats score, lower ML score (statistical outlier)
        ML_PATTERN_ANOMALY: High ML score, lower stats score (pattern-based)
        HYBRID_CONFIRMED: Both scores high (strong confirmation)
        NORMAL: Combined score below threshold
        """
        if combined_score < self.COMBINED_THRESHOLD:
            return CauseEnum.NORMAL

        stats_dominant = stats_score > (ml_score + 0.2)
        ml_dominant = ml_score > (stats_score + 0.2)

        if stats_dominant:
            return CauseEnum.STATISTICAL_SPIKE
        elif ml_dominant:
            return CauseEnum.ML_PATTERN_ANOMALY
        else:
            return CauseEnum.HYBRID_CONFIRMED

    def _generate_explanations(
        self,
        transaction: Transaction,
        stats_score: float,
        ml_score: float,
        combined_score: float,
        cause: CauseEnum,
    ) -> tuple[str, str]:
        """Generate human-readable explanations for anomaly"""
        base_explanation = f"Amount: {transaction.amount}, Category: {transaction.category}. "
        base_explanation += f"Statistical score: {stats_score:.2f}, ML score: {ml_score:.2f}, Combined: {combined_score:.2f}. "

        if cause == CauseEnum.STATISTICAL_SPIKE:
            base_explanation += "Detected as statistical outlier (unusual magnitude)."
            advice = "Review transaction amount against historical category averages."
        elif cause == CauseEnum.ML_PATTERN_ANOMALY:
            base_explanation += "Detected as pattern anomaly (uncommon behavior)."
            advice = "Check if this represents a new legitimate business pattern."
        elif cause == CauseEnum.HYBRID_CONFIRMED:
            base_explanation += "Confirmed anomaly by both statistical and pattern methods."
            advice = "High confidence anomaly - prioritize for investigation."
        else:
            base_explanation += "Within normal parameters."
            advice = "No action needed."

        return base_explanation, advice

    def _determine_severity(self, combined_score: float) -> SeverityEnum:
        """Determine severity level based on combined score"""
        if combined_score >= self.SEVERITY_HIGH:
            return SeverityEnum.HIGH
        elif combined_score >= self.SEVERITY_MEDIUM:
            return SeverityEnum.MEDIUM
        else:
            return SeverityEnum.LOW
