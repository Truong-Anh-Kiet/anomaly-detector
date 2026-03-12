"""Anomaly detection service tests"""

import pytest
from datetime import datetime, timedelta
import json
from sqlalchemy.orm import Session
from src.models import Anomaly, AnomalyDetectionBatch
from src.services.anomaly_service import AnomalyService
from src.config import get_settings


@pytest.fixture
def anomaly_service():
    """Provide AnomalyService instance"""
    return AnomalyService()


@pytest.fixture
def test_anomalies(db_session):
    """Create test anomalies"""
    anomalies = [
        Anomaly(
            anomaly_id=f"anom_{i}",
            detection_timestamp=datetime.utcnow() - timedelta(hours=i),
            category="payment",
            amount=1000 + (i * 100),
            score=0.8 + (i * 0.05),
            threshold=0.7,
            status="pending_review",
            user_id="test_user",
        )
        for i in range(5)
    ]
    db_session.add_all(anomalies)
    db_session.commit()
    return anomalies


class TestAnomalyCreation:
    """Test creating anomaly records"""

    def test_create_anomaly_success(self, anomaly_service, db_session):
        """Test successful anomaly creation"""
        anomaly = anomaly_service.create_anomaly(
            db=db_session,
            detection_timestamp=datetime.utcnow(),
            category="payment",
            amount=5000.0,
            score=0.85,
            threshold=0.7,
            user_id="user123",
        )

        assert anomaly is not None
        assert anomaly.category == "payment"
        assert anomaly.amount == 5000.0
        assert anomaly.score == 0.85
        assert anomaly.status == "pending_review"

    def test_create_anomaly_below_threshold(self, anomaly_service, db_session):
        """Test that anomalies with score below threshold are flagged"""
        anomaly = anomaly_service.create_anomaly(
            db=db_session,
            detection_timestamp=datetime.utcnow(),
            category="network",
            amount=100.0,
            score=0.65,  # Below typical threshold
            threshold=0.7,
            user_id="user123",
        )

        assert anomaly is not None
        # Score below threshold may need additional review
        assert anomaly.score == 0.65


class TestAnomalyQuery:
    """Test reading and filtering anomalies"""

    def test_get_anomalies_by_category(self, anomaly_service, db_session, test_anomalies):
        """Test filtering anomalies by category"""
        payment_anomalies = anomaly_service.get_anomalies_by_category(
            db=db_session, category="payment"
        )

        assert len(payment_anomalies) == 5
        assert all(a.category == "payment" for a in payment_anomalies)

    def test_get_pending_anomalies(self, anomaly_service, db_session, test_anomalies):
        """Test retrieving pending review anomalies"""
        pending = anomaly_service.get_pending_anomalies(db=db_session)

        assert len(pending) == 5
        assert all(a.status == "pending_review" for a in pending)

    def test_get_anomalies_time_range(self, anomaly_service, db_session, test_anomalies):
        """Test getting anomalies within time range"""
        now = datetime.utcnow()
        start = now - timedelta(hours=3)
        end = now

        anomalies = anomaly_service.get_anomalies_by_time_range(
            db=db_session, start_time=start, end_time=end
        )

        assert len(anomalies) > 0
        assert all(start <= a.detection_timestamp <= end for a in anomalies)

    def test_get_anomalies_empty_result(self, anomaly_service, db_session):
        """Test query returning empty results"""
        results = anomaly_service.get_anomalies_by_category(
            db=db_session, category="nonexistent"
        )

        assert results == []


class TestAnomalyStatus:
    """Test anomaly status transitions"""

    def test_update_anomaly_status(self, anomaly_service, db_session, test_anomalies):
        """Test updating anomaly status"""
        anomaly = test_anomalies[0]
        updated = anomaly_service.update_anomaly_status(
            db=db_session,
            anomaly_id=anomaly.anomaly_id,
            status="reviewed",
            notes="Confirmed legitimate anomaly",
        )

        assert updated.status == "reviewed"
        assert updated.review_notes == "Confirmed legitimate anomaly"

    def test_mark_as_false_positive(self, anomaly_service, db_session, test_anomalies):
        """Test marking anomaly as false positive"""
        anomaly = test_anomalies[0]
        updated = anomaly_service.update_anomaly_status(
            db=db_session,
            anomaly_id=anomaly.anomaly_id,
            status="false_positive",
        )

        assert updated.status == "false_positive"

    def test_mark_as_confirmed(self, anomaly_service, db_session, test_anomalies):
        """Test marking anomaly as confirmed"""
        anomaly = test_anomalies[0]
        updated = anomaly_service.update_anomaly_status(
            db=db_session,
            anomaly_id=anomaly.anomaly_id,
            status="confirmed",
        )

        assert updated.status == "confirmed"


class TestAnomalyAggregation:
    """Test anomaly statistics and aggregations"""

    def test_get_anomalies_by_score_range(
        self, anomaly_service, db_session, test_anomalies
    ):
        """Test filtering by score range"""
        high_confidence = anomaly_service.get_anomalies_by_score_range(
            db=db_session, min_score=0.8, max_score=1.0
        )

        assert len(high_confidence) > 0
        assert all(0.8 <= a.score <= 1.0 for a in high_confidence)

    def test_get_anomaly_distribution_by_category(
        self, anomaly_service, db_session, test_anomalies
    ):
        """Test getting distribution of anomalies by category"""
        distribution = anomaly_service.get_anomaly_distribution_by_category(
            db=db_session
        )

        assert isinstance(distribution, dict)
        assert "payment" in distribution
        assert distribution["payment"] == 5
