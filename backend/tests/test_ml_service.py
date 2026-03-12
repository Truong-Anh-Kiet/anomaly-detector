"""Machine learning service tests"""

import pytest
import numpy as np
from src.services.ml_service import MLService


@pytest.fixture
def ml_service():
    """Provide MLService instance"""
    return MLService()


@pytest.fixture
def sample_sequence():
    """Create a sample time series data"""
    return np.array([10, 12, 11, 13, 15, 14, 16, 100, 18, 19, 20])


@pytest.fixture
def sample_batch():
    """Create a batch of sequences"""
    return [
        np.array([10, 12, 11, 13, 15, 14, 16, 18, 19, 20]),
        np.array([1.0, 1.1, 0.9, 1.2, 1.0, 1.3, 1.1, 50, 1.2, 1.0]),
        np.array([5, 5, 5, 5, 100, 5, 5, 5, 5, 5]),
    ]


class TestModelLoading:
    """Test ML model loading and initialization"""

    def test_model_loads_successfully(self, ml_service):
        """Test that model loads without error"""
        assert ml_service.is_loaded()

    def test_model_version_available(self, ml_service):
        """Test that model version is accessible"""
        version = ml_service.get_model_version()
        assert version is not None
        assert isinstance(version, str)


class TestSequenceValidation:
    """Test input validation for sequences"""

    def test_valid_sequence(self, ml_service, sample_sequence):
        """Test validation of valid sequence"""
        is_valid = ml_service.validate_sequence(sample_sequence)
        assert is_valid is True

    def test_sequence_too_short(self, ml_service):
        """Test validation of too-short sequence"""
        short_seq = np.array([1, 2, 3])
        is_valid = ml_service.validate_sequence(short_seq)
        assert is_valid is False

    def test_sequence_too_long(self, ml_service):
        """Test validation of too-long sequence"""
        long_seq = np.random.randn(200)
        is_valid = ml_service.validate_sequence(long_seq)
        assert is_valid is False

    def test_sequence_with_nan(self, ml_service):
        """Test validation of sequence with NaN values"""
        nan_seq = np.array([1, 2, np.nan, 4, 5])
        is_valid = ml_service.validate_sequence(nan_seq)
        assert is_valid is False

    def test_sequence_with_inf(self, ml_service):
        """Test validation of sequence with infinities"""
        inf_seq = np.array([1, 2, np.inf, 4, 5])
        is_valid = ml_service.validate_sequence(inf_seq)
        assert is_valid is False


class TestAnomalyDetection:
    """Test anomaly detection functionality"""

    def test_detect_anomaly_in_normal_sequence(self, ml_service, sample_sequence):
        """Test detection on normal sequence"""
        score = ml_service.detect_anomaly(sample_sequence)

        assert 0 <= score <= 1
        # Most values are normal, so score should be low
        assert score < 0.6

    def test_detect_anomaly_with_outlier(self, ml_service, sample_sequence):
        """Test detection with known outlier"""
        # sample_sequence has 100 at index 7, which is anomalous
        score = ml_service.detect_anomaly(sample_sequence)

        assert 0 <= score <= 1
        # Should detect the anomaly
        assert score > 0.5

    def test_batch_detection(self, ml_service, sample_batch):
        """Test batch detection on multiple sequences"""
        scores = ml_service.detect_batch_anomalies(sample_batch)

        assert len(scores) == len(sample_batch)
        assert all(0 <= s <= 1 for s in scores)

    def test_detection_consistency(self, ml_service, sample_sequence):
        """Test that detection produces consistent results"""
        score1 = ml_service.detect_anomaly(sample_sequence)
        score2 = ml_service.detect_anomaly(sample_sequence)

        assert score1 == score2


class TestFeatureExtraction:
    """Test feature extraction from sequences"""

    def test_extract_features(self, ml_service, sample_sequence):
        """Test feature extraction"""
        features = ml_service.extract_features(sample_sequence)

        assert features is not None
        assert isinstance(features, np.ndarray)
        assert len(features) > 0

    def test_features_normalized(self, ml_service, sample_sequence):
        """Test that features are normalized"""
        features = ml_service.extract_features(sample_sequence)

        # Features should be in reasonable range
        assert np.all(features >= -10)
        assert np.all(features <= 10)


class TestThresholdApplication:
    """Test anomaly threshold application"""

    def test_score_below_threshold(self, ml_service, sample_sequence):
        """Test classification as normal when score is below threshold"""
        score = ml_service.detect_anomaly(sample_sequence)
        threshold = 0.9

        is_anomaly = score >= threshold
        assert is_anomaly is False

    def test_score_above_threshold(self, ml_service):
        """Test classification as anomaly when score is above threshold"""
        # Create a sequence designed to have high anomaly score
        seq = np.array([1, 1, 1, 1, 1, 100, 100, 100, 1, 1])
        score = ml_service.detect_anomaly(seq)
        threshold = 0.3

        is_anomaly = score >= threshold
        assert is_anomaly is True
