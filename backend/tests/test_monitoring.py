"""Monitoring and observability tests"""

import pytest
from datetime import datetime, timedelta
from src.services.monitoring import (
    PerformanceMonitor,
    HealthChecker,
    MetricsCollector,
)


@pytest.fixture
def performance_monitor():
    """Provide PerformanceMonitor instance"""
    return PerformanceMonitor()


@pytest.fixture
def health_checker():
    """Provide HealthChecker instance"""
    return HealthChecker()


@pytest.fixture
def metrics_collector():
    """Provide MetricsCollector instance"""
    return MetricsCollector()


class TestPerformanceMonitoring:
    """Test performance metric recording and analysis"""

    def test_record_single_metric(self, performance_monitor):
        """Test recording a single performance metric"""
        performance_monitor.record_metric(
            endpoint="/anomalies",
            method="GET",
            duration_ms=25.5,
            status_code=200,
            user_id="user123",
        )

        assert len(performance_monitor.metrics) == 1
        metric = performance_monitor.metrics[0]
        assert metric.endpoint == "/anomalies"
        assert metric.duration_ms == 25.5
        assert metric.status_code == 200

    def test_record_multiple_metrics(self, performance_monitor):
        """Test recording multiple metrics"""
        for i in range(5):
            performance_monitor.record_metric(
                endpoint="/anomalies",
                method="GET",
                duration_ms=10 + i,
                status_code=200,
            )

        assert len(performance_monitor.metrics) == 5

    def test_record_error_metric(self, performance_monitor):
        """Test recording error metric"""
        performance_monitor.record_metric(
            endpoint="/models/upload",
            method="POST",
            duration_ms=100,
            status_code=500,
            error="Database connection failed",
        )

        metric = performance_monitor.metrics[0]
        assert metric.error == "Database connection failed"
        assert metric.status_code == 500

    def test_metrics_window_size(self, performance_monitor):
        """Test that metrics window is maintained"""
        monitor = PerformanceMonitor(window_size=10)

        # Record 15 metrics
        for i in range(15):
            monitor.record_metric(
                endpoint="/anomalies",
                method="GET",
                duration_ms=10,
                status_code=200,
            )

        # Should keep only 10 most recent
        assert len(monitor.metrics) == 10


class TestEndpointStats:
    """Test endpoint statistics calculation"""

    def test_get_endpoint_stats(self, performance_monitor):
        """Test calculating stats for an endpoint"""
        durations = [10, 20, 30, 40, 50]

        for duration in durations:
            performance_monitor.record_metric(
                endpoint="/anomalies",
                method="GET",
                duration_ms=duration,
                status_code=200,
            )

        stats = performance_monitor.get_endpoint_stats(endpoint="/anomalies")

        assert stats["count"] == 5
        assert stats["avg_duration_ms"] == 30
        assert stats["min_duration_ms"] == 10
        assert stats["max_duration_ms"] == 50
        assert stats["error_rate"] == 0

    def test_endpoint_stats_with_errors(self, performance_monitor):
        """Test stats with some error responses"""
        performance_monitor.record_metric(
            endpoint="/models/upload", method="POST", duration_ms=100, status_code=200
        )
        performance_monitor.record_metric(
            endpoint="/models/upload", method="POST", duration_ms=150, status_code=500
        )
        performance_monitor.record_metric(
            endpoint="/models/upload", method="POST", duration_ms=120, status_code=500
        )

        stats = performance_monitor.get_endpoint_stats(endpoint="/models/upload")

        assert stats["count"] == 3
        assert stats["error_rate"] == 2 / 3

    def test_get_all_endpoint_stats(self, performance_monitor):
        """Test getting stats for all endpoints"""
        performance_monitor.record_metric(
            endpoint="/anomalies", method="GET", duration_ms=10, status_code=200
        )
        performance_monitor.record_metric(
            endpoint="/models", method="GET", duration_ms=20, status_code=200
        )

        stats = performance_monitor.get_endpoint_stats(endpoint=None)

        # When endpoint=None, it should aggregate all
        assert stats["count"] >= 2


class TestSlowestEndpoints:
    """Test identification of slowest endpoints"""

    def test_get_slowest_endpoints(self, performance_monitor):
        """Test identifying slowest endpoints"""
        # /anomalies: avg 25ms
        for duration in [20, 30]:
            performance_monitor.record_metric(
                endpoint="/anomalies", method="GET", duration_ms=duration, status_code=200
            )

        # /models: avg 100ms
        for duration in [90, 110]:
            performance_monitor.record_metric(
                endpoint="/models", method="GET", duration_ms=duration, status_code=200
            )

        slowest = performance_monitor.get_slowest_endpoints(limit=10)

        assert len(slowest) == 2
        assert slowest[0]["endpoint"] == "/models"
        assert slowest[0]["avg_duration_ms"] == 100
        assert slowest[1]["endpoint"] == "/anomalies"


class TestHealthStatus:
    """Test health check functionality"""

    def test_initial_health_status(self, health_checker):
        """Test initial health status"""
        status = health_checker.get_status()

        assert status["healthy"] is True
        assert status["components"]["database"] is True
        assert status["components"]["ml_model"] is True

    def test_unhealthy_database(self, health_checker):
        """Test unhealthy database"""
        health_checker.set_status("database", False)

        assert health_checker.is_healthy() is False

    def test_unhealthy_ml_model(self, health_checker):
        """Test unhealthy ML model"""
        health_checker.set_status("ml_model", False)

        assert health_checker.is_healthy() is False

    def test_unhealthy_non_critical_component(self, health_checker):
        """Test that non-critical component doesn't affect overall health"""
        health_checker.set_status("cache", False)

        # Should still be healthy since cache is not critical
        assert health_checker.is_healthy() is True

    def test_get_health_status_dict(self, health_checker):
        """Test getting health status as dictionary"""
        health_checker.set_status("database", True)
        health_checker.set_status("ml_model", True)

        status = health_checker.get_status()

        assert "healthy" in status
        assert "components" in status
        assert "last_checked" in status
        assert "timestamp" in status


class TestMetricsCollection:
    """Test metrics collection and aggregation"""

    def test_increment_counter(self, metrics_collector):
        """Test counter increment"""
        metrics_collector.increment_counter("api_requests")
        metrics_collector.increment_counter("api_requests", 5)

        metrics = metrics_collector.get_metrics()
        assert metrics["counters"]["api_requests"] == 6

    def test_set_gauge(self, metrics_collector):
        """Test gauge setting"""
        metrics_collector.set_gauge("queue_size", 42.0)
        metrics_collector.set_gauge("queue_size", 50.0)

        metrics = metrics_collector.get_metrics()
        assert metrics["gauges"]["queue_size"] == 50.0

    def test_record_histogram(self, metrics_collector):
        """Test histogram recording"""
        values = [10, 20, 30, 40, 50]
        for v in values:
            metrics_collector.record_histogram("response_time", float(v))

        metrics = metrics_collector.get_metrics()
        hist = metrics["histograms"]["response_time"]

        assert hist["count"] == 5
        assert hist["min"] == 10
        assert hist["max"] == 50
        assert hist["avg"] == 30

    def test_reset_metrics(self, metrics_collector):
        """Test resetting all metrics"""
        metrics_collector.increment_counter("requests")
        metrics_collector.set_gauge("cpu", 50.0)
        metrics_collector.record_histogram("latency", 100.0)

        metrics_collector.reset()

        metrics = metrics_collector.get_metrics()
        assert len(metrics["counters"]) == 0
        assert len(metrics["gauges"]) == 0
        assert len(metrics["histograms"]) == 0
